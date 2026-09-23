"""M3E offline probes: synthetic scalar results, no credentials/network/Revit."""
import ast
import copy
import json
import unittest
import test_bimcode_ai_tool as old
import test_bimcode_piping_ai_tools as piping
import test_bimcode_hvac_ai_tools as hvac
from bimcode_ai_pane import ai_tool_registry as registry

EXPECTED = {
    'summarize_selected_electrical_elements': 'ELECTRICAL-RO-001-A01',
    'inspect_selected_electrical_connectors': 'ELECTRICAL-RO-001-A02',
    'inspect_selected_electrical_circuit_assignment': 'ELECTRICAL-RO-001-A03',
    'inspect_selected_electrical_qa_health': 'ELECTRICAL-RO-001-A04',
}


def result_for(name, profile='DEVICE_PROFILE'):
    return dict(ok=True, action_id=EXPECTED[name], specialty='ELECTRICAL',
                classification='ELECTRICAL_QA_HEALTH_YELLOW', reason_code='COMPLETE',
                selected_reference_count=1, resolved_selected_count=1,
                summary=['Deterministic issue count: 1', 'Partial check count: 0'],
                electrical_checks=[dict(check_id='ELECTRICAL-QA-003', issues=1, affected_ids=['42'])],
                generic_checks=[dict(check_id='SEL-QA-001', issues=0)],
                warnings=['Authoritative warning'], warnings_total=1,
                tables=[['Authoritative records',
                         ['Element id', 'Profile', 'Role', 'Relationship', 'Read state',
                          'System id', 'Panel', 'Circuit', 'Voltage V', 'Power factor', 'Domain'],
                         [['42', profile, 'LOAD' if profile == 'DEVICE_PROFILE' else 'BASE_EQUIPMENT',
                           'UPSTREAM_OR_LOAD_CIRCUIT' if profile == 'DEVICE_PROFILE' else 'DOWNSTREAM_BRANCH_CIRCUIT',
                           'NOT_APPLICABLE', '43', 'Panel A', '2', 230, 0.9, 'DomainElectrical']]]])


class ProviderTests(unittest.TestCase):
    send = old.ProviderTests.send

    def test_exact_twelve_and_strict_schemas(self):
        expected = dict(piping.EXPECTED, **hvac.EXPECTED); expected.update(EXPECTED)
        self.assertEqual(registry.ACTIONS, expected)
        self.assertEqual(old.tool_protocol.ACTIONS, expected)
        self.assertEqual({t['name'] for t in old.provider.TOOLS}, set(expected))
        self.assertEqual(len(old.provider.TOOLS), 12)
        for tool in old.provider.TOOLS:
            self.assertTrue(tool['strict'])
            self.assertEqual(tool['parameters'], dict(type='object', properties={}, required=[], additionalProperties=False))

    def test_closed_mappings(self):
        source = (old.ROOT / 'AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py').read_text(encoding='utf-8-sig')
        tree = ast.parse(source.replace('.None', '._None'))
        node = next(n for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'ELECTRICAL_RO_001_ACTION_METADATA' for t in n.targets))
        self.assertEqual(set(ast.literal_eval(node.value).values()), {
            ('ELECTRICAL-RO-001-A01', 'show selected electrical elements summary'),
            ('ELECTRICAL-RO-001-A02', 'show selected electrical connectors'),
            ('ELECTRICAL-RO-001-A03', 'check selected electrical circuit assignment'),
            ('ELECTRICAL-RO-001-A04', 'check selected electrical elements qa health')})

    def test_continuations_and_loop_guard(self):
        for name, action in EXPECTED.items():
            response = self.send([old.output_call(name=name)])
            self.assertEqual(response, piping.response(name))
            self.assertTrue(self.client.responses.create.call_args.kwargs['store'])
            req = old.request('tool_result', tool_call=response['tool_call'], provider_state=response['provider_state'],
                              tool_result=old.ai_tool.compact(result_for(name), action))
            self.assertEqual(old.protocol.parse(json.dumps(req)), req)
            self.assertEqual(self.send(req=req)['state'], 'FINAL')
            args = self.client.responses.create.call_args.kwargs
            self.assertEqual((args['store'], args['tools'], args['tool_choice']), (False, [], 'none'))
            self.assertEqual(args['previous_response_id'], 'resp_1')
            self.assertEqual(args['input'][0]['call_id'], 'call_1')
            self.assertEqual(json.loads(args['input'][0]['output']), req['tool_result'])
            self.assertEqual(self.send([old.output_call(name=name)], req=req)['error']['code'], 'AI_TOOL_LOOP_LIMIT')
            self.assertEqual(self.send([old.output_call(name=name), old.output_call()])['error']['code'], 'AI_TOOL_LOOP_LIMIT')

    def test_argument_overrides_rejected(self):
        for name in EXPECTED:
            for key in ('action_id', 'ElementId', 'document_id', 'path', 'script', 'command', 'url', 'profile', 'category', 'specialty'):
                self.assertEqual(self.send([old.output_call(name=name, arguments=json.dumps({key: 'bad'}))])['error']['code'], 'AI_TOOL_ARGUMENTS_INVALID')


class ProjectionTests(unittest.TestCase):
    def test_device_equipment_scalar_parity(self):
        for name, action in EXPECTED.items():
            for profile in ('DEVICE_PROFILE', 'EQUIPMENT_PROFILE'):
                value = result_for(name, profile); before = copy.deepcopy(value)
                result = old.ai_tool.compact(value, action)
                self.assertEqual(value, before)
                for key in value:
                    if key != 'ok': self.assertEqual(result[key], value[key])

    def test_caps_and_oversized_core(self):
        for name, action in EXPECTED.items():
            value = result_for(name); value['electrical_checks'] *= 40
            value['tables'][0][2] *= 100
            result = old.ai_tool.compact(value, action)
            self.assertEqual(result['transport_omissions']['electrical_checks'], 10)
            self.assertEqual(result['transport_omissions']['table_rows'], 60)
            self.assertEqual(result['electrical_checks'], value['electrical_checks'][:30])
            value['summary'] = ['x' * 8000] * 11
            with self.assertRaises(ValueError): old.ai_tool.compact(value, action)

    def test_wrong_provenance_rejected(self):
        for name, action in EXPECTED.items():
            for field, bad in (('specialty', 'HVAC'), ('action_id', 'PIPING-RO-001-A01')):
                value = result_for(name); value[field] = bad
                with self.assertRaises(ValueError): old.ai_tool.compact(value, action)


class CoordinatorTests(unittest.TestCase):
    setUp = old.CoordinatorTests.setUp

    def run_tool(self, name, specialties, unsupported=0, stale=None):
        self.coordinator.clear(); self.coordinator.begin(old.RID)
        self.document_key.return_value = self.session.document_identity
        self.execute_headless_modelmind_readonly.reset_mock()
        self.execute_headless_modelmind_readonly.return_value = result_for(name)
        self.resolve_headless_modelmind_specialty.return_value = dict(ok=True, specialties=specialties, unsupported_count=unsupported)
        self.done.reset_mock()
        response = piping.response(name)
        if stale == 'document': self.document_key.return_value = ('other',)
        elif stale == 'request': response['request_id'] = 'c' * 32
        elif stale: setattr(self.session, stale, getattr(self.session, stale) + 1)
        self.coordinator.queue(response, self.done)
        self.execute_headless_modelmind_readonly.assert_not_called()
        self.coordinator.execute_approved(self.uiapp)

    def test_exact_action_once(self):
        for name, action in EXPECTED.items():
            self.run_tool(name, ['ELECTRICAL'])
            self.execute_headless_modelmind_readonly.assert_called_once_with(action, self.uiapp.ActiveUIDocument.Document, self.uiapp.ActiveUIDocument)
            self.assertIsNone(self.done.call_args.args[0])
            self.coordinator.queue(piping.response(name), self.done)
            self.coordinator.execute_approved(self.uiapp)
            self.assertEqual(self.execute_headless_modelmind_readonly.call_count, 1)

    def test_cross_specialty_and_unsupported_only(self):
        for name in EXPECTED:
            for scope in (['PIPING'], ['HVAC'], ['PIPING', 'ELECTRICAL'], ['HVAC', 'ELECTRICAL'], ['PIPING', 'HVAC', 'ELECTRICAL'], []):
                self.run_tool(name, scope, 1 if not scope else 0)
                self.execute_headless_modelmind_readonly.assert_not_called()
                self.assertEqual(self.done.call_args.args[0]['error']['code'], 'AI_TOOL_NOT_ALLOWED')

    def test_stale_guards(self):
        for name in EXPECTED:
            for field in ('document', 'context_generation', 'selection_generation', 'request'):
                self.run_tool(name, ['ELECTRICAL'], stale=field)
                self.execute_headless_modelmind_readonly.assert_not_called()


if __name__ == '__main__': unittest.main()
