"""M3D offline tests. Fake results only; no credentials, network or Revit."""
import ast
import copy
import json
import unittest

import test_bimcode_ai_tool as old
import test_bimcode_piping_ai_tools as piping
from bimcode_ai_pane import ai_tool_registry as registry

EXPECTED = {
    'summarize_selected_ducts': 'HVAC-RO-001-A01',
    'inspect_selected_duct_connectors': 'HVAC-RO-001-A02',
    'inspect_selected_duct_system_assignment': 'HVAC-RO-001-A03',
    'inspect_selected_duct_qa_health': 'HVAC-RO-001-A04',
}


def result_for(name):
    action = EXPECTED[name]
    number = action[-2:]
    value = dict(ok=True, action_id=action, specialty='HVAC', reason_code='COMPLETE',
                 selected_reference_count=1, resolved_selected_count=1,
                 classification={'01': 'HVAC_SELECTION_SUMMARY_OK',
                                 '02': 'HVAC_CONNECTOR_REPORT_OK',
                                 '03': 'HVAC_SYSTEM_ASSIGNMENT_OK',
                                 '04': 'HVAC_QA_HEALTH_YELLOW'}[number],
                 warnings=['Authoritative warning'], warnings_total=1,
                 connector_rows_truncated=False, warning_display_truncated=False)
    value['summary'] = {
        '01': ['Supported rigid non-placeholder ducts: 1', 'Total readable duct length: 1000 mm'],
        '02': ['Total raw connector count: 3', 'Physical HVAC connector count: 3',
               'Physical End connectors: 2', 'Physical non-End connectors: 1'],
        '03': ['ASSIGNED: 1', 'INCONSISTENT: 0'],
        '04': ['Deterministic issue count: 1', 'Partial check count: 0']}[number]
    value['tables'] = {
        '01': [['Supported rigid duct records',
                ['Element id', 'Duct type', 'Shape', 'Width mm', 'Height mm', 'Length mm',
                 'Slope state', 'Reference level', 'System name', 'Insulation', 'Lining'],
                [['358702', 'Default', 'Rectangular', 400, 200, 1000, 'VERTICAL', 'Level 1',
                  'Mechanical Supply Air 2', 'NONE', 'NONE']]]],
        '02': [['Physical HVAC connector details',
                ['Element id', 'Type', 'Shape', 'Dimensions', 'Origin', 'Direction',
                 'Reciprocal connection', 'Connected owners', 'Unreadable'],
                [['358702', 'End', 'Rectangular', '400 x 200 mm', '0,0,0', '1,0,0', True, ['42'], 0],
                 ['358702', 'Curve', 'Round', '100 mm', '1,0,0', '0,1,0', True, ['43'], 0]]]],
        '03': [['Normalized system metadata',
                ['State', 'System name', 'System type', 'Classification', 'MEP system ID',
                 'Consistency', 'Contradictions'],
                [['ASSIGNED', 'Mechanical Supply Air 2', 'Supply Air', 'SupplyAir',
                  '358704', 'CONSISTENT', []]]]],
        '04': [['Selection scope classification', ['Scope', 'Count'], [['SUPPORTED_DUCT', 1]]]],
    }[number]
    if number == '04':
        value['hvac_checks'] = [dict(check_id='HVAC-QA-009', status='PASS', issues=0, affected_ids=[])]
        value['generic_checks'] = [dict(check_id='SEL-QA-011', status='ISSUES_FOUND', issues=1,
                                        affected_ids=['358702'])]
    return value


class RegistryProviderTests(unittest.TestCase):
    send = old.ProviderTests.send

    def test_exact_eight_static_tools(self):
        expected = dict(piping.EXPECTED, **EXPECTED)
        self.assertEqual(registry.ACTIONS, expected)
        self.assertEqual(old.tool_protocol.ACTIONS, expected)
        self.assertEqual(len(old.provider.TOOLS), 8)
        self.assertEqual({t['name'] for t in old.provider.TOOLS}, set(expected))

    def test_strict_empty_schemas(self):
        for tool in old.provider.TOOLS:
            self.assertTrue(tool['strict'])
            self.assertEqual(tool['parameters'], dict(type='object', properties={}, required=[], additionalProperties=False))

    def test_closed_canonical_mapping(self):
        source = (old.ROOT / 'AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py').read_text(encoding='utf-8-sig')
        tree = ast.parse(source.replace('.None', '._None'))
        assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'HVAC_RO_001_ACTION_METADATA' for t in n.targets))
        self.assertEqual(set(ast.literal_eval(assignment.value).values()), {
            ('HVAC-RO-001-A01', 'show selected ducts summary'),
            ('HVAC-RO-001-A02', 'show selected duct connectors'),
            ('HVAC-RO-001-A03', 'check selected ducts system assignment'),
            ('HVAC-RO-001-A04', 'check selected ducts qa health')})

    def test_all_model_calls_and_continuations(self):
        for name, action in EXPECTED.items():
            response = self.send([old.output_call(name=name)])
            self.assertEqual(response, piping.response(name))
            initial = self.client.responses.create.call_args.kwargs
            self.assertTrue(initial['store'])
            self.assertFalse(initial['parallel_tool_calls'])
            req = old.request('tool_result', tool_call=response['tool_call'], provider_state=response['provider_state'],
                              tool_result=old.ai_tool.compact(result_for(name), action))
            self.assertEqual(old.protocol.parse(json.dumps(req)), req)
            self.assertEqual(self.send(req=req)['state'], 'FINAL')
            args = self.client.responses.create.call_args.kwargs
            self.assertFalse(args['store'])
            self.assertEqual(args['tools'], [])
            self.assertEqual(args['tool_choice'], 'none')
            self.assertEqual(args['previous_response_id'], 'resp_1')
            self.assertEqual(args['input'][0]['call_id'], 'call_1')
            self.assertEqual(json.loads(args['input'][0]['output']), req['tool_result'])
            self.assertEqual(self.send([old.output_call(name=name)], req=req)['error']['code'], 'AI_TOOL_LOOP_LIMIT')

    def test_nonempty_arguments_cannot_override(self):
        for name in EXPECTED:
            for key in ('action_id', 'ElementId', 'document_id', 'path', 'command', 'script', 'url', 'specialty', 'executable'):
                args = {key: 'override'}
                self.assertEqual(self.send([old.output_call(name=name, arguments=json.dumps(args))])['error']['code'], 'AI_TOOL_ARGUMENTS_INVALID')
                response = piping.response(name); response['tool_call']['arguments'] = args
                self.assertEqual(old.provider_bridge.decode(json.dumps(response), old.RID, 0)['error']['code'], 'AI_TOOL_ARGUMENTS_INVALID')

    def test_multiple_cross_specialty_calls_rejected(self):
        for name in EXPECTED:
            self.assertEqual(self.send([old.output_call(name=name), old.output_call()])['error']['code'], 'AI_TOOL_LOOP_LIMIT')

    def test_wrong_specialty_and_action_rejected(self):
        for name, action in EXPECTED.items():
            response = piping.response(name)
            for field, bad in (('specialty', 'PIPING'), ('action_id', 'PIPING-RO-001-A01')):
                value = result_for(name); value[field] = bad
                with self.assertRaises(ValueError): old.ai_tool.compact(value, action)
                req = old.request('tool_result', tool_call=response['tool_call'], provider_state=response['provider_state'], tool_result=value)
                with self.assertRaises(old.tool_protocol.ToolError): old.protocol.parse(json.dumps(req))

    def test_policy_specialty_and_end_curve_authority(self):
        instruction = old.provider.TOOL_INSTRUCTION
        for text in ('HVAC-QA-009', 'End connectors', 'Curve/tap', 'Never recompute',
                     'Never use either for electrical', 'Mixed Pipe+Duct', 'single supported specialty', 'At most one'):
            self.assertIn(text, instruction)


class CoordinatorTests(unittest.TestCase):
    setUp = old.CoordinatorTests.setUp

    def run_tool(self, name, scope=None, stale=None):
        self.coordinator.clear(); self.coordinator.begin(old.RID)
        self.document_key.return_value = self.session.document_identity
        self.execute_headless_modelmind_readonly.reset_mock()
        self.execute_headless_modelmind_readonly.return_value = result_for(name)
        self.resolve_headless_modelmind_specialty.return_value = scope or dict(ok=True, specialties=['HVAC'])
        self.done.reset_mock()
        response = piping.response(name)
        if stale == 'document': self.document_key.return_value = ('other',)
        elif stale == 'request': response['request_id'] = 'c' * 32
        elif stale: setattr(self.session, stale, getattr(self.session, stale) + 1)
        self.coordinator.queue(response, self.done)
        self.execute_headless_modelmind_readonly.assert_not_called()
        self.coordinator.execute_approved(self.uiapp)

    def test_four_actions_execute_once_with_exact_parity(self):
        for name, action in EXPECTED.items():
            self.run_tool(name)
            self.execute_headless_modelmind_readonly.assert_called_once_with(action, self.uiapp.ActiveUIDocument.Document, self.uiapp.ActiveUIDocument)
            error, result = self.done.call_args.args
            self.assertIsNone(error)
            for key, value in result_for(name).items():
                if key != 'ok': self.assertEqual(result[key], value)
            self.coordinator.queue(piping.response(name), self.done)
            self.coordinator.execute_approved(self.uiapp)
            self.assertEqual(self.done.call_args.args[0]['error']['code'], 'AI_TOOL_LOOP_LIMIT')
            self.assertEqual(self.execute_headless_modelmind_readonly.call_count, 1)

    def test_all_stale_guards(self):
        for name in EXPECTED:
            for field in ('document', 'context_generation', 'selection_generation', 'request'):
                self.run_tool(name, stale=field)
                self.execute_headless_modelmind_readonly.assert_not_called()
                self.assertEqual(self.done.call_args.args[0]['error']['code'],
                                 'AI_TOOL_PROTOCOL_ERROR' if field == 'request' else 'STALE_CONTEXT')

    def test_cross_specialty_mixed_and_unsupported_rejected(self):
        for name in EXPECTED:
            for specialties, unsupported in ((['PIPING'], 0), (['ELECTRICAL'], 0),
                    (['PIPING', 'HVAC'], 0), (['HVAC', 'ELECTRICAL'], 0), ([], 1)):
                self.run_tool(name, dict(ok=True, specialties=specialties, unsupported_count=unsupported))
                self.execute_headless_modelmind_readonly.assert_not_called()
                self.assertEqual(self.done.call_args.args[0]['error']['code'], 'AI_TOOL_NOT_ALLOWED')

    def test_supported_plus_unsupported_still_owned_by_builder(self):
        for name in EXPECTED:
            self.run_tool(name, dict(ok=True, specialties=['HVAC'], unsupported_count=1))
            self.execute_headless_modelmind_readonly.assert_called_once()

    def test_scope_failure_no_execution(self):
        for name in EXPECTED:
            self.run_tool(name, dict(ok=False))
            self.execute_headless_modelmind_readonly.assert_not_called()


class ProjectionTests(unittest.TestCase):
    def test_all_fields_unchanged_and_no_recomputation(self):
        for name, action in EXPECTED.items():
            value = result_for(name); before = copy.deepcopy(value)
            result = old.ai_tool.compact(value, action)
            self.assertEqual(value, before)
            for key in value:
                if key != 'ok': self.assertEqual(result[key], value[key])

    def test_hvac_checks_and_warnings_caps_disclosed(self):
        name = 'inspect_selected_duct_qa_health'; value = result_for(name)
        value['hvac_checks'] *= 40; value['warnings'] *= 40
        result = old.ai_tool.compact(value, EXPECTED[name])
        for key in ('hvac_checks', 'warnings'):
            self.assertEqual(result[key], value[key][:30])
            self.assertEqual(result['transport_omissions'][key], 10)
        self.assertEqual(result['summary'], value['summary'])

    def test_bounded_details_and_omission_metadata(self):
        for name, action in EXPECTED.items():
            value = result_for(name); value['tables'][0][2] *= 100
            result = old.ai_tool.compact(value, action)
            self.assertEqual(len(result['tables'][0][2]), 40)
            self.assertEqual(result['transport_omissions']['table_rows'], len(value['tables'][0][2]) - 40)
            self.assertLessEqual(len(json.dumps(result)), 80000)

    def test_oversized_core_fails_closed(self):
        for name, action in EXPECTED.items():
            value = result_for(name); value['summary'] = ['x' * 8000] * 11
            with self.assertRaises(ValueError): old.ai_tool.compact(value, action)

    def test_hvac_provenance(self):
        for name, action, label in registry.TOOLS[4:]:
            result = old.protocol.success(old.RID, 'test-model', 'Explanation')
            value = result_for(name)
            result['tool_provenance'] = {k: value[k] for k in ('action_id', 'classification', 'reason_code')}
            blocks = old.provider_ui.presentation(result)['blocks']
            self.assertTrue(any(b['label'] == 'Tool used: ' and b['text'] == label for b in blocks))


class PaneTests(unittest.TestCase):
    setUp = old.PaneTests.setUp
    ready = old.PaneTests.ready
    start_ai = old.PaneTests.start_ai

    def test_four_sequential_hvac_turns(self):
        for name, action in EXPECTED.items():
            self.start_ai()
            response = piping.response(name); response['request_id'] = self.rid
            self.panel._provider_complete(response)
            self.assertTrue(self.coordinator.pending)
            self.assertFalse(self.panel.FindName('SendButton').IsEnabled)
            self.coordinator.complete(None, old.ai_tool.compact(result_for(name), action))
            request = self.launch.call_args.args[0]
            self.assertEqual(request['tool_result']['action_id'], action)
            self.panel._provider_complete(old.protocol.success(self.rid, 'test-model', 'Explanation'))
            self.assertIsNone(self.coordinator.turn)
            self.assertIn(registry.LABELS[action], str(self.panel._presentation))


if __name__ == '__main__': unittest.main()
