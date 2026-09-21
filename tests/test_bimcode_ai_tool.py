"""M3B offline tests; no credentials/config files/network/Revit instance."""
import ast
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "BIMCode_Provider"))
sys.path.insert(0, str(ROOT / "AI.extension/lib"))
import provider
import protocol
import tool_protocol
from provider_config import Config
from bimcode_ai_pane import ai_tool, provider_bridge, provider_ui
import test_bimcode_provider as m3a
import test_bimcode_ai_pane as m1

RID = "b" * 32


def request(op="agent_turn", **kwargs):
    result = dict(protocol_version=1, request_id=RID, operation=op)
    if op == "agent_turn":
        result["user_text"] = "Summarize the selected pipe."
    result.update(kwargs)
    return result


def intermediate():
    result = protocol.success(RID, "test-model", None)
    result.update(state="TOOL_REQUEST", tool_call=dict(call_id="call_1", name=tool_protocol.NAME, arguments={}),
                  provider_state=dict(response_id="resp_1", model="test-model"))
    return result


def data():
    return dict(ok=True, action_id=ai_tool.ACTION, specialty="PIPING",
                classification="PIPING_SELECTION_SUMMARY_OK", reason_code="COMPLETE",
                summary=["Supported: 1", "Length: 23000.0 mm"], tables=[], warnings=[])


def followup():
    call = intermediate()
    return request("tool_result", tool_call=call["tool_call"], provider_state=call["provider_state"], tool_result=ai_tool.compact(data()))


def output_call(**kwargs):
    fields = dict(type="function_call", name=tool_protocol.NAME, arguments="{}", call_id="call_1")
    fields.update(kwargs)
    return types.SimpleNamespace(**fields)


class ProviderTests(unittest.TestCase):
    def send(self, items=(), text="answer", req=None, error=None):
        self.client = Mock()
        self.client.responses.create.return_value = types.SimpleNamespace(status="completed", id="resp_1", output=list(items), output_text=text)
        self.client.responses.create.side_effect = error
        factory = Mock()
        factory.return_value.__enter__ = Mock(return_value=self.client)
        factory.return_value.__exit__ = Mock(return_value=False)
        return provider.send(Config("READY", "fake-offline-key", "test-model"), req or request(), factory)

    def test_plain_final(self):
        result = self.send()
        self.assertEqual(result["state"], "FINAL")
        self.assertEqual(result["text"], "answer")

    def test_tool_schema_exact(self):
        self.send()
        args = self.client.responses.create.call_args.kwargs
        self.assertEqual(args["tools"], provider.TOOLS)
        self.assertEqual(provider.TOOL["name"], tool_protocol.NAME)
        self.assertEqual(provider.TOOL["parameters"], dict(type="object", properties={}, required=[], additionalProperties=False))
        self.assertTrue(provider.TOOL["strict"])
        self.assertEqual(args["tool_choice"], "auto")
        self.assertFalse(args["parallel_tool_calls"])
        self.assertTrue(args["store"])

    def test_call_extraction(self):
        self.assertEqual(self.send([output_call()]), intermediate())

    def test_unknown_tool(self):
        self.assertEqual(self.send([output_call(name="delete")])["error"]["code"], "AI_TOOL_NOT_ALLOWED")

    def test_arguments(self):
        for args in ('{"action_id":"HVAC-RO-001-A01"}', '[]', 'null', 'bad', None):
            self.assertEqual(self.send([output_call(arguments=args)])["error"]["code"], "AI_TOOL_ARGUMENTS_INVALID")

    def test_bad_call_id(self):
        self.assertEqual(self.send([output_call(call_id=None)])["error"]["code"], "AI_TOOL_PROTOCOL_ERROR")

    def test_multiple_calls(self):
        self.assertEqual(self.send([output_call(), output_call()])["error"]["code"], "AI_TOOL_LOOP_LIMIT")

    def test_unexpected_builtin(self):
        self.assertEqual(self.send([types.SimpleNamespace(type="web_search_call")])["error"]["code"], "AI_TOOL_NOT_ALLOWED")

    def test_continuation(self):
        result = self.send(req=followup())
        args = self.client.responses.create.call_args.kwargs
        self.assertEqual(args["previous_response_id"], "resp_1")
        self.assertEqual(args["input"][0]["call_id"], "call_1")
        self.assertEqual(args["input"][0]["type"], "function_call_output")
        self.assertEqual(json.loads(args["input"][0]["output"]), followup()["tool_result"])
        self.assertEqual(args["tools"], [])
        self.assertEqual(args["tool_choice"], "none")
        self.assertFalse(args["store"])
        self.assertEqual(result["state"], "FINAL")

    def test_second_tool_blocked(self):
        self.assertEqual(self.send([output_call()], req=followup())["error"]["code"], "AI_TOOL_LOOP_LIMIT")

    def test_model_drift(self):
        req = followup(); req["provider_state"]["model"] = "different"
        self.assertEqual(self.send(req=req)["error"]["code"], "AI_TOOL_PROTOCOL_ERROR")
        self.client.responses.create.assert_not_called()

    def test_continuation_error(self):
        self.assertEqual(self.send(req=followup(), error=RuntimeError("private"))["error"]["code"], "INTERNAL_PROVIDER_ERROR")

    def test_empty_final(self):
        self.assertEqual(self.send(req=followup(), text="")["error"]["code"], "OPENAI_EMPTY_RESPONSE")


class ProtocolTests(unittest.TestCase):
    def test_roundtrip(self):
        for req in (request(), followup()):
            self.assertEqual(protocol.parse(json.dumps(req)), req)

    def test_no_generic_dispatch(self):
        req = request(action_id="HVAC-RO-001-A01")
        with self.assertRaises(tool_protocol.ToolError):
            protocol.parse(json.dumps(req))

    def test_result_bound(self):
        req = followup(); req["tool_result"]["summary"] = ["x" * 80000]
        with self.assertRaises(tool_protocol.ToolError):
            protocol.parse(json.dumps(req))

    def test_host_decoder(self):
        self.assertEqual(provider_bridge.decode(json.dumps(intermediate()), RID, 0), intermediate())
        result = protocol.success(RID, "model", "answer"); result["state"] = "FINAL"
        self.assertTrue(provider_bridge.decode(json.dumps(result), RID, 0)["ok"])

    def test_host_rejects(self):
        for field, value, code in (("name", "hvac", "AI_TOOL_NOT_ALLOWED"),
                                   ("arguments", {"action_id": "x"}, "AI_TOOL_ARGUMENTS_INVALID"),
                                   ("call_id", None, "AI_TOOL_PROTOCOL_ERROR")):
            response = intermediate(); response["tool_call"][field] = value
            self.assertEqual(provider_bridge.decode(json.dumps(response), RID, 0)["error"]["code"], code)

    def test_host_correlation(self):
        self.assertEqual(provider_bridge.decode(json.dumps(intermediate()), "c" * 32, 0)["error"]["code"], "SIDECAR_REQUEST_ID_MISMATCH")


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.session = types.SimpleNamespace(document_identity=(1,"doc","path"), context_generation=1,
                                             selection_generation=1, tools=types.SimpleNamespace(pending=None),
                                             raise_ai_event=Mock(return_value=True))
        self.coordinator = ai_tool.Coordinator(self.session)
        self.coordinator.begin(RID)
        self.done = Mock()
        self.uiapp = types.SimpleNamespace(ActiveUIDocument=types.SimpleNamespace(Document=object()))
        for name, value in (("document_key",self.session.document_identity),
                            ("resolve_headless_modelmind_specialty",dict(ok=True,specialties=["PIPING"])),
                            ("execute_headless_modelmind_readonly",data())):
            p = patch.object(ai_tool,name,return_value=value); mock=p.start();self.addCleanup(p.stop);setattr(self,name,mock)

    def execute(self):
        self.coordinator.queue(intermediate(),self.done)
        self.coordinator.execute_approved(self.uiapp)

    def test_one_action_parity(self):
        self.execute()
        self.execute_headless_modelmind_readonly.assert_called_once_with(ai_tool.ACTION,self.uiapp.ActiveUIDocument.Document,self.uiapp.ActiveUIDocument)
        error, result = self.done.call_args.args
        self.assertIsNone(error)
        for key in ('classification','reason_code','summary','action_id','specialty'):
            self.assertEqual(result[key],data()[key])

    def test_no_background_or_queue_execution(self):
        self.coordinator.queue(intermediate(),self.done)
        self.execute_headless_modelmind_readonly.assert_not_called()

    def test_stale_document(self):
        self.document_key.return_value=(2,"other","path")
        self.execute()
        self.assertEqual(self.done.call_args.args[0]["error"]["code"],"STALE_CONTEXT")
        self.execute_headless_modelmind_readonly.assert_not_called()

    def test_stale_generation(self):
        self.session.context_generation+=1;self.execute()
        self.assertEqual(self.done.call_args.args[0]["error"]["code"],"STALE_CONTEXT")

    def test_stale_selection(self):
        self.session.selection_generation+=1;self.execute()
        self.assertEqual(self.done.call_args.args[0]["error"]["code"],"STALE_CONTEXT")

    def test_wrong_request(self):
        response=intermediate();response['request_id']='c'*32
        self.coordinator.queue(response,self.done)
        self.assertEqual(self.done.call_args.args[0]["error"]["code"],"AI_TOOL_PROTOCOL_ERROR")

    def test_loop_limit(self):
        self.execute();self.coordinator.queue(intermediate(),self.done)
        self.assertEqual(self.done.call_args.args[0]["error"]["code"],"AI_TOOL_LOOP_LIMIT")
        self.coordinator.execute_approved(self.uiapp)
        self.execute_headless_modelmind_readonly.assert_called_once()

    def test_gate(self):
        self.assertFalse(self.coordinator.begin('c'*32))
        self.coordinator.clear();self.session.tools.pending={}
        self.assertFalse(self.coordinator.begin(RID))

    def test_modelmind_failure(self):
        self.execute_headless_modelmind_readonly.side_effect=RuntimeError('private')
        self.execute()
        self.assertEqual(self.done.call_args.args[0]["error"]["code"],"MODELMIND_EXECUTION_FAILED")

    def test_duct_never_executes_piping(self):
        self.resolve_headless_modelmind_specialty.return_value=dict(ok=True,specialties=['HVAC'])
        self.execute();self.execute_headless_modelmind_readonly.assert_not_called()
        self.assertEqual(self.done.call_args.args[0]["error"]["code"],"AI_TOOL_NOT_ALLOWED")

    def test_empty_owned_by_builder_mixed_rejected(self):
        for specialties in ([],['PIPING','HVAC']):
            self.coordinator.clear();self.coordinator.begin(RID)
            self.resolve_headless_modelmind_specialty.return_value=dict(ok=True,specialties=specialties)
            self.execute()
        self.assertEqual(self.execute_headless_modelmind_readonly.call_count,1)
        self.assertEqual(self.done.call_args.args[0]['error']['code'], 'AI_TOOL_NOT_ALLOWED')

    def test_raise_rejected(self):
        self.session.raise_ai_event.return_value=False
        self.execute()
        self.assertFalse(self.coordinator.pending)
        self.execute_headless_modelmind_readonly.assert_not_called()

    def test_projection_rejects_object(self):
        value=data();value['summary']=[object()]
        with self.assertRaises(ValueError):ai_tool.compact(value)

    def test_projection_bound_and_omissions(self):
        value=data();value['tables']=[['Pipes',['Id'],[[i] for i in range(100)]]]
        result=ai_tool.compact(value)
        self.assertEqual(result['transport_omissions']['table_rows'],60)
        self.assertEqual(len(result['tables'][0][2]),40)
        self.assertEqual(len(value['tables'][0][2]),100)


class PaneTests(unittest.TestCase):
    setUp = m3a.PaneTests.setUp
    ready = m3a.PaneTests.ready
    def start_ai(self):
        self.ready()
        self.session=types.SimpleNamespace(document_identity=None,context_generation=0,selection_generation=0,
                                          tools=types.SimpleNamespace(pending=None),raise_ai_event=Mock(return_value=True))
        self.coordinator=ai_tool.Coordinator(self.session)
        self.panel.bind_ai(self.coordinator)
        self.panel._on_send(None,None)
        self.rid=self.launch.call_args.args[0]['request_id']

    def test_ai_plain_response(self):
        self.start_ai()
        self.assertEqual(self.launch.call_args.args[0]['operation'],'agent_turn')
        self.panel._provider_complete(protocol.success(self.rid,'test-model','answer'))
        self.assertIsNone(self.coordinator.turn)
        self.assertTrue(self.panel.FindName('SendButton').IsEnabled)
        self.assertNotIn('Tool used',str(self.panel._presentation))

    def test_ai_tool_roundtrip(self):
        self.start_ai();response=intermediate();response['request_id']=self.rid
        self.panel._provider_complete(response)
        self.assertTrue(self.coordinator.pending)
        self.assertFalse(self.panel.FindName('SendButton').IsEnabled)
        self.coordinator.complete(None,ai_tool.compact(data()))
        self.assertEqual(self.launch.call_args.args[0]['operation'],'tool_result')
        self.panel._provider_complete(protocol.success(self.rid,'test-model','answer'))
        self.assertIsNone(self.coordinator.turn)
        self.assertIn(ai_tool.ACTION,str(self.panel._presentation))
        self.assertTrue(self.panel.FindName('SummaryButton').IsEnabled)

    def test_ai_failure_recovers(self):
        self.start_ai();response=intermediate();response['request_id']=self.rid
        self.panel._provider_complete(response)
        self.coordinator.complete(provider_bridge.failure(self.rid,'STALE_CONTEXT'),None)
        self.assertIsNone(self.coordinator.turn)
        self.assertTrue(self.panel.FindName('SendButton').IsEnabled)
        self.assertIn('STALE_CONTEXT',str(self.panel._presentation))

    def test_second_tool_response_releases_gate(self):
        self.start_ai();response=intermediate();response['request_id']=self.rid
        self.panel._provider_complete(response)
        self.coordinator.complete(None,ai_tool.compact(data()))
        self.panel._provider_complete(response)
        self.assertIsNone(self.coordinator.turn)
        self.assertIn('AI_TOOL_LOOP_LIMIT',str(self.panel._presentation))
        self.assertTrue(self.panel.FindName('SendButton').IsEnabled)

    def test_continuation_failure_preserves_provenance(self):
        self.start_ai();response=intermediate();response['request_id']=self.rid
        self.panel._provider_complete(response)
        self.coordinator.complete(None,ai_tool.compact(data()))
        self.panel._provider_complete(provider_bridge.failure(self.rid,'OPENAI_TIMEOUT'))
        self.assertIn(ai_tool.ACTION,str(self.panel._presentation))
        self.assertIsNone(self.coordinator.turn)
        self.assertTrue(self.panel.FindName('SendButton').IsEnabled)


class LifecycleIntegrationTests(unittest.TestCase):
    setUp = m1.LifecycleTests.setUp
    tearDown = m1.LifecycleTests.tearDown
    register = m1.LifecycleTests.register

    def test_existing_external_event_dispatches_ai_only_when_pending(self):
        session=self.module.PaneSession(self.uiapp)
        session.ai.begin(RID)
        session.ai.queue(intermediate(),Mock())
        with patch.object(session.ai,'execute_approved') as execute:
            session.tool_handler.Execute(self.uiapp)
            execute.assert_called_once_with(self.uiapp)
        self.assertIsNone(session.tools.pending)

    def test_selection_event_invalidates_ai_without_changing_m2_generation(self):
        session=self.module.PaneSession(self.uiapp)
        before=session.context_generation
        session.ai.begin(RID)
        session.on_selection_changed(None,types.SimpleNamespace(GetSelectedElements=lambda:types.SimpleNamespace(Count=1)))
        self.assertEqual(session.selection_generation,1)
        self.assertEqual(session.context_generation,before)
        self.assertEqual(session.ai.turn['selection'],0)


class BoundaryTests(unittest.TestCase):
    def test_execution_owner(self):
        tree=ast.parse((ROOT/'AI.extension/lib/bimcode_ai_pane/lifecycle.py').read_text())
        owners=[n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)
                for c in ast.walk(n) if isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and c.func.attr=='execute_approved']
        self.assertEqual(owners,['Execute'])

    def test_literal_action_and_no_mutation(self):
        tree=ast.parse((ROOT/'AI.extension/lib/bimcode_ai_pane/ai_tool.py').read_text())
        literals=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and '-RO-001-A' in n.value]
        self.assertEqual(literals,[])  # Literal mappings now live in the fixed registry.
        names={n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
        self.assertFalse(names & {'Transaction','TransactionGroup','SetElementIds','Set','Delete','Create'})


if __name__=='__main__':unittest.main()
