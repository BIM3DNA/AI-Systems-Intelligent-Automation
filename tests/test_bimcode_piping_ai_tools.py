"""M3C offline four-tool coverage. No config, credentials, network or Revit."""
import ast
import copy
import json
import unittest
from unittest.mock import Mock

import test_bimcode_ai_tool as old
from bimcode_ai_pane import ai_tool_registry as registry

EXPECTED = {
    'summarize_selected_pipes': 'PIPING-RO-001-A01',
    'inspect_selected_pipe_connectors': 'PIPING-RO-001-A02',
    'inspect_selected_pipe_system_assignment': 'PIPING-RO-001-A03',
    'inspect_selected_pipe_qa_health': 'PIPING-RO-001-A04',
}


def response(name):
    result = old.intermediate()
    result['tool_call']['name'] = name
    return result


def result_for(name):
    result = old.data()
    result['action_id'] = EXPECTED[name]
    number = result['action_id'][-2:]
    result['classification'] = {
        '01': 'PIPING_SELECTION_SUMMARY_OK', '02': 'PIPING_CONNECTOR_REPORT_OK',
        '03': 'PIPING_SYSTEM_ASSIGNMENT_OK', '04': 'PIPING_QA_HEALTH_YELLOW'}[number]
    result['summary'] = {
        '01': ['Supported rigid pipes: 1', 'Total readable pipe length: 1 ft / 304.8 mm'],
        '02': ['Total raw connector count: 2', 'Physical piping connector count: 2',
               'Reciprocally connected physical connector count: 0', 'Unconnected physical connector count: 2'],
        '03': ['UNASSIGNED_REVIEW pipe IDs: none', 'INCONSISTENT pipe IDs: none'],
        '04': ['Deterministic issue count: 2', 'Partial check count: 0']}[number]
    result['tables'] = {
        '01': [['Pipe type distribution', ['Type', 'Count'], [['Default', 1]]],
               ['Supported rigid pipe records', ['Id', 'Segment', 'Diameter mm', 'Slope', 'Level'],
                [['1', 'Steel', 150, 0, 'Level 1']]]],
        '02': [['Per-pipe connector summary', ['Pipe id', 'Raw', 'Physical'], [['1', 2, 2]]],
               ['Physical piping connector details', ['Owner', 'Raw IsConnected', 'Reciprocal physical connection'],
                [['1', False, 'false']]]],
        '03': [['System assignment state distribution', ['Value', 'Stable id', 'Count'], [['ASSIGNED', '', 1]]],
               ['Per-pipe normalized system metadata', ['State', 'System type', 'System name'],
                [['ASSIGNED', 'Hydronic Supply', 'Hydronic Supply 5']]]],
        '04': [['Selection scope classification', ['Scope', 'Count'], [['SUPPORTED_PIPE', 1]]]]}[number]
    result['warnings'] = ['Authoritative warning']
    if number == '04':
        result['piping_checks'] = [dict(check_id='PIPING-QA-010', status='ISSUES_FOUND', issues=2,
                                        passed=0, skipped=0, affected_ids=['1'], omitted_ids=0)]
        result['generic_checks'] = [dict(check_id='SEL-QA-001', status='PASS', issues=0)]
    return result


class RegistryProviderTests(unittest.TestCase):
    send = old.ProviderTests.send

    def test_exact_registry_and_schemas(self):
        self.assertEqual({k: v for k, v in registry.ACTIONS.items() if k in EXPECTED}, EXPECTED)
        self.assertEqual({k: v for k, v in old.tool_protocol.ACTIONS.items() if k in EXPECTED}, EXPECTED)
        self.assertEqual(len(old.provider.TOOLS), 12)
        self.assertEqual({t['name'] for t in old.provider.TOOLS[:4]}, set(EXPECTED))
        descriptions = ('summary', 'connector report', 'system-assignment report', 'QA-health report')
        for tool, report in zip(old.provider.TOOLS, descriptions):
            self.assertEqual(tool, dict(type='function', name=tool['name'], strict=True,
                description='Return the deterministic read-only {0} for currently selected supported rigid Revit pipes.'.format(report),
                parameters=dict(type='object', properties={}, required=[], additionalProperties=False)))

    def test_four_model_selected_calls(self):
        for name in EXPECTED:
            with self.subTest(name=name):
                self.assertEqual(self.send([old.output_call(name=name)]), response(name))
                args = self.client.responses.create.call_args.kwargs
                self.assertEqual(args['tools'], old.provider.TOOLS)
                self.assertEqual(args['tool_choice'], 'auto')
                self.assertFalse(args['parallel_tool_calls'])

    def test_no_keyword_routing(self):
        for prompt in ('What is pipe slope?', 'Check these selected pipes.',
                       'Check selected duct connectors.', 'Check electrical equipment.'):
            value = self.send(req=old.request(user_text=prompt), text='Explanation or clarification')
            self.assertEqual(value['state'], 'FINAL')
            self.assertNotIn('tool_call', value)
            self.assertEqual(self.client.responses.create.call_args.kwargs['input'], prompt)

    def test_all_continuations_disable_tools(self):
        for name, action in EXPECTED.items():
            value = response(name)
            req = old.request('tool_result', tool_call=value['tool_call'], provider_state=value['provider_state'],
                              tool_result=old.ai_tool.compact(result_for(name), action))
            self.assertEqual(old.protocol.parse(json.dumps(req)), req)
            self.assertEqual(self.send(req=req)['state'], 'FINAL')
            args = self.client.responses.create.call_args.kwargs
            self.assertEqual(args['tools'], [])
            self.assertEqual(args['tool_choice'], 'none')
            self.assertFalse(args['store'])
            self.assertEqual(json.loads(args['input'][0]['output']), req['tool_result'])
            self.assertEqual(self.send([old.output_call(name=name)], req=req)['error']['code'], 'AI_TOOL_LOOP_LIMIT')

    def test_different_tools_in_same_response_rejected(self):
        names = list(EXPECTED)
        for name in names:
            self.assertEqual(self.send([old.output_call(name=name), old.output_call(name=names[-1])])['error']['code'],
                             'AI_TOOL_LOOP_LIMIT')

    def test_bad_names_and_arguments_both_boundaries(self):
        for name in ('inspect_selected_flex_duct_connectors', 'inspect_selected_electrical_qa', 'delete_pipes', '', [], None):
            self.assertEqual(self.send([old.output_call(name=name)])['error']['code'], 'AI_TOOL_NOT_ALLOWED')
            self.assertEqual(old.provider_bridge.decode(json.dumps(response(name)), old.RID, 0)['error']['code'], 'AI_TOOL_NOT_ALLOWED')
        for name in EXPECTED:
            for argument in ('{"action_id":"PIPING-RO-001-A04"}', '{"ElementId":1}', '[]', 'null'):
                self.assertEqual(self.send([old.output_call(name=name, arguments=argument)])['error']['code'], 'AI_TOOL_ARGUMENTS_INVALID')
                value = response(name); value['tool_call']['arguments'] = json.loads(argument)
                self.assertEqual(old.provider_bridge.decode(json.dumps(value), old.RID, 0)['error']['code'], 'AI_TOOL_ARGUMENTS_INVALID')

    def test_result_action_must_match_call(self):
        for name in EXPECTED:
            req = old.followup()
            req['tool_call']['name'] = name
            req['tool_result']['action_id'] = 'PIPING-RO-001-A04' if name == old.ai_tool.NAME else old.ai_tool.ACTION
            with self.assertRaises(old.tool_protocol.ToolError):
                old.protocol.parse(json.dumps(req))

    def test_policy_preserves_qa_and_ambiguity(self):
        instruction = old.provider.TOOL_INSTRUCTION
        for text in ('authoritative', 'clarification', 'YELLOW', 'partial/unreadable', 'At most one', 'Never use either for electrical'):
            self.assertIn(text, instruction)


class FourActionCoordinatorTests(unittest.TestCase):
    setUp = old.CoordinatorTests.setUp

    def reset(self, name):
        self.coordinator.clear()
        self.coordinator.begin(old.RID)
        self.execute_headless_modelmind_readonly.reset_mock()
        self.execute_headless_modelmind_readonly.return_value = result_for(name)
        self.done.reset_mock()

    def execute(self, name):
        self.coordinator.queue(response(name), self.done)
        self.execute_headless_modelmind_readonly.assert_not_called()
        self.coordinator.execute_approved(self.uiapp)

    def test_each_exact_action_once_with_parity(self):
        for name, action in EXPECTED.items():
            self.reset(name); self.execute(name)
            self.execute_headless_modelmind_readonly.assert_called_once_with(action, self.uiapp.ActiveUIDocument.Document, self.uiapp.ActiveUIDocument)
            error, data = self.done.call_args.args
            self.assertIsNone(error)
            for key in ('summary', 'tables', 'warnings', 'classification', 'reason_code', 'action_id'):
                self.assertEqual(data[key], result_for(name)[key])
            self.coordinator.queue(response(name), self.done)
            self.assertEqual(self.done.call_args.args[0]['error']['code'], 'AI_TOOL_LOOP_LIMIT')
            self.coordinator.execute_approved(self.uiapp)
            self.assertEqual(self.execute_headless_modelmind_readonly.call_count, 1)

    def test_each_stale_boundary(self):
        for name in EXPECTED:
            for field in ('document', 'context_generation', 'selection_generation'):
                self.document_key.return_value = self.session.document_identity
                self.reset(name)
                if field == 'document': self.document_key.return_value = ('other',)
                else: setattr(self.session, field, getattr(self.session, field) + 1)
                self.execute(name)
                self.assertEqual(self.done.call_args.args[0]['error']['code'], 'STALE_CONTEXT')
                self.execute_headless_modelmind_readonly.assert_not_called()

    def test_each_request_correlation(self):
        for name in EXPECTED:
            self.reset(name)
            value = response(name); value['request_id'] = 'c' * 32
            self.coordinator.queue(value, self.done)
            self.coordinator.execute_approved(self.uiapp)
            self.assertEqual(self.done.call_args.args[0]['error']['code'], 'AI_TOOL_PROTOCOL_ERROR')
            self.execute_headless_modelmind_readonly.assert_not_called()

    def test_each_rejects_duct_and_electrical(self):
        for name in EXPECTED:
            for specialty in ('HVAC', 'ELECTRICAL'):
                self.reset(name)
                self.resolve_headless_modelmind_specialty.return_value = dict(ok=True, specialties=[specialty])
                self.execute(name)
                self.assertEqual(self.done.call_args.args[0]['error']['code'], 'AI_TOOL_NOT_ALLOWED')
                self.execute_headless_modelmind_readonly.assert_not_called()

    def test_each_rejects_wrong_result_action(self):
        for name in EXPECTED:
            self.reset(name)
            self.execute_headless_modelmind_readonly.return_value['action_id'] = 'HVAC-RO-001-A01'
            self.execute(name)
            self.assertEqual(self.done.call_args.args[0]['error']['code'], 'MODELMIND_EXECUTION_FAILED')

    def test_each_no_document(self):
        self.session.document_identity = None
        self.document_key.return_value = None
        for name in EXPECTED:
            self.reset(name); self.execute(name)
            self.assertEqual(self.done.call_args.args[0]['error']['code'], 'MODELMIND_NOT_READY')
            self.execute_headless_modelmind_readonly.assert_not_called()


class ProjectionPresentationTests(unittest.TestCase):
    def test_existing_list_caps_disclosed(self):
        value = result_for('inspect_selected_pipe_qa_health')
        value['warnings'] *= 40
        value['piping_checks'] *= 40
        value['warnings_total'] = 40
        result = old.ai_tool.compact(value, EXPECTED['inspect_selected_pipe_qa_health'])
        for key in ('warnings', 'piping_checks'):
            self.assertEqual(result[key], value[key][:30])
            self.assertEqual(result['transport_omissions'][key], 10)
        self.assertEqual(result['summary'], value['summary'])
        self.assertEqual(result['warnings_total'], 40)

    def test_all_fields_preserved_without_recalculation(self):
        for name, action in EXPECTED.items():
            value = result_for(name); before = copy.deepcopy(value)
            result = old.ai_tool.compact(value, action)
            self.assertEqual(value, before)
            for key in value:
                if key != 'ok': self.assertEqual(result[key], value[key])

    def test_detail_budget_fair_and_explicit(self):
        for name, action in EXPECTED.items():
            value = result_for(name)
            value['tables'] = [[title, headers, rows * 100] for title, headers, rows in value['tables']]
            result = old.ai_tool.compact(value, action)
            shown = sum(len(t[2]) for t in result['tables'])
            total = sum(len(t[2]) for t in value['tables'])
            self.assertEqual(shown, 40)
            self.assertTrue(all(t[2] for t in result['tables']))
            self.assertEqual(result['transport_omissions']['table_rows'], total - shown)
            self.assertEqual(sum(t['rows'] for t in result['transport_omissions']['tables']), total - shown)
            self.assertEqual(result['summary'], value['summary'])
            self.assertEqual(result['warnings'], value['warnings'])

    def test_table_cap(self):
        value = old.data(); value['tables'] = [['Detail', ['Id'], [[i]]] for i in range(20)]
        result = old.ai_tool.compact(value)
        self.assertEqual(len(result['tables']), 12)
        self.assertEqual(result['transport_omissions']['table_rows'], 8)

    def test_oversized_details_not_core_removed(self):
        name = 'inspect_selected_pipe_qa_health'
        value = result_for(name); value['tables'] = [['Details', ['Text'], [['x' * 8000] for i in range(40)]]]
        result = old.ai_tool.compact(value, EXPECTED[name])
        self.assertNotIn('tables', result)
        self.assertTrue(result['transport_omissions']['tables_field'])
        self.assertEqual(result['transport_omissions']['table_rows'], 40)
        for key in ('summary', 'warnings', 'piping_checks', 'generic_checks', 'classification'):
            self.assertEqual(result[key], value[key])
        self.assertLessEqual(len(json.dumps(result, ensure_ascii=True)), 80000)

    def test_oversized_core_fails_closed(self):
        value = old.data(); value['summary'] = ['x' * 8000 for i in range(11)]
        with self.assertRaises(ValueError): old.ai_tool.compact(value)

    def test_exact_provenance_and_no_raw_json(self):
        for name, action, label in registry.TOOLS[:4]:
            result = old.protocol.success(old.RID, 'test-model', 'Readable explanation')
            value = result_for(name)
            result['tool_provenance'] = {key: value[key] for key in ('action_id', 'classification', 'reason_code')}
            blocks = old.provider_ui.presentation(result)['blocks']
            self.assertTrue(any(b['label'] == 'Tool used: ' and b['text'] == label for b in blocks))
            for field in result['tool_provenance'].values(): self.assertIn(field, str(blocks))
            self.assertNotIn('tables', str(blocks))

    def test_no_mutation_or_network_added(self):
        for filename in ('ai_tool.py', 'ai_tool_registry.py', 'provider_ui.py'):
            tree = ast.parse((old.ROOT / 'AI.extension/lib/bimcode_ai_pane' / filename).read_text())
            attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
            self.assertFalse(attrs & {'Transaction', 'TransactionGroup', 'SetElementIds', 'Set', 'Delete', 'Create', 'urlopen', 'requests'})


class FourActionPaneTests(unittest.TestCase):
    setUp = old.PaneTests.setUp
    ready = old.PaneTests.ready
    start_ai = old.PaneTests.start_ai

    def test_four_sequential_turns_followup_and_provenance(self):
        for name, action, label in registry.TOOLS[:4]:
            self.start_ai()
            value = response(name); value['request_id'] = self.rid
            self.panel._provider_complete(value)
            self.assertTrue(self.coordinator.pending)
            self.assertFalse(self.panel.FindName('SendButton').IsEnabled)
            payload = old.ai_tool.compact(result_for(name), action)
            self.coordinator.complete(None, payload)
            req = self.launch.call_args.args[0]
            self.assertEqual(req['operation'], 'tool_result')
            self.assertEqual(req['tool_call']['name'], name)
            self.assertEqual(req['tool_result']['action_id'], action)
            self.panel._provider_complete(old.protocol.success(self.rid, 'test-model', 'Readable explanation'))
            self.assertIsNone(self.coordinator.turn)
            self.assertIn(label, str(self.panel._presentation))
            for button in ('SummaryButton', 'ConnectorsButton', 'AssignmentButton', 'QAButton'):
                self.assertTrue(self.panel.FindName(button).IsEnabled)

    def test_each_continuation_error_preserves_provenance(self):
        for name, action, label in registry.TOOLS[:4]:
            self.start_ai()
            value = response(name); value['request_id'] = self.rid
            self.panel._provider_complete(value)
            self.coordinator.complete(None, old.ai_tool.compact(result_for(name), action))
            self.panel._provider_complete(old.provider_bridge.failure(self.rid, 'OPENAI_TIMEOUT'))
            self.assertIsNone(self.coordinator.turn)
            self.assertIn(label, str(self.panel._presentation))
            self.assertTrue(self.panel.FindName('SendButton').IsEnabled)


if __name__ == '__main__': unittest.main()
