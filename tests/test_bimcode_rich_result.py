"""Rich renderer presentation tests; no Revit/model/network access."""
import ast
import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'AI.extension/lib'))
from bimcode_ai_pane import result_presentation as presentation
from bimcode_ai_pane import theme


def fixture(tool='selection.system_assignment'):
    # Scalar fixture shaped exactly like production Piping A03 tables. Not a
    # fabricated live Revit result; no model/element construction in these tests.
    return dict(tool_name=tool, status='OK', specialty='PIPING',
        classification='PIPING_SYSTEM_ASSIGNMENT_OK', reason_code='COMPLETE', data=dict(
            selected_reference_count=2, summary=['Total selected references: 2',
            'Supported rigid pipes: 2', 'Supported pipes processed: 2',
            'Unsupported or unresolved selected references: 0'], warnings=[], tables=[
            ['System assignment state distribution', ['Value', 'Stable id', 'Count'], [['ASSIGNED', '', 2]]],
            ['System name distribution', ['Value', 'Stable id', 'Count'], [['Hydronic Supply 1', '', 1], ['Hydronic Supply 5', '', 1]]],
            ['System classification distribution', ['Value', 'Stable id', 'Count'], [['Hydronic Supply', '', 2]]],
            ['Per-pipe normalized system metadata', ['Assignment state', 'System type', 'System name',
                'MEP system id', 'Pipe id', 'Classification', 'Built-in metadata', 'Fallback metadata',
                'Consistency', 'Authoritative sources', 'Contradictions'], [
                ['ASSIGNED', 'Hydronic Supply', 'Hydronic Supply 1', '358679', '358677',
                 'Hydronic Supply', 'built in', 'fallback', 'CONSISTENT', 'MEPSystem', 'none'],
                ['ASSIGNED', 'Hydronic Supply', 'Hydronic Supply 5', '353873', '353871',
                 'Hydronic Supply', 'built in', 'fallback', 'CONSISTENT', 'MEPSystem', 'none']]]]))


def text(model):
    return '\n'.join(block['label'] + block['text'] for block in model['blocks'])


class RichPresentationTests(unittest.TestCase):
    def test_ok_title(self):
        self.assertEqual(presentation.build_presentation(fixture())['blocks'][0]['text'], 'System Assignment')

    def test_specialty_and_reason_metadata(self):
        output = text(presentation.build_presentation(fixture()))
        self.assertIn('PIPING', output)
        self.assertIn('COMPLETE', output)

    def test_production_classification_visible(self):
        blocks = presentation.build_presentation(fixture())['blocks']
        block = next(b for b in blocks if b['text'] == 'PIPING_SYSTEM_ASSIGNMENT_OK')
        self.assertEqual(block['kind'], 'technical')
        self.assertEqual(block['tone'], 'SecondaryTextBrush')

    def test_reason_preserved(self):
        value = fixture()
        value['reason_code'] = 'ORIGINAL_REASON'
        self.assertIn('Reason: ORIGINAL_REASON', text(presentation.build_presentation(value)))

    def test_summary_promoted_before_details(self):
        output = text(presentation.build_presentation(fixture('selection.summary')))
        self.assertLess(output.index('Supported rigid pipes: 2'), output.index('Details'))

    def test_warnings_preserved_before_details(self):
        value = fixture()
        value['data']['warnings'] = ['First warning', 'Second warning']
        output = text(presentation.build_presentation(value))
        self.assertIn('First warning', output)
        self.assertLess(output.index('Second warning'), output.index('Details'))

    def test_no_warnings_clean(self):
        self.assertIn('Warnings\nNone', text(presentation.build_presentation(fixture())))

    def test_empty_selection_no_empty_sections(self):
        output = text(presentation.build_presentation(dict(tool_name='selection.summary', status='NOT_READY', reason_code='NO_ELEMENTS_SELECTED')))
        self.assertIn('Selection Summary', output)
        self.assertIn('NOT READY', output)
        self.assertIn('No elements selected.', output)
        self.assertIn('\nWarnings\nNone reported', output)
        self.assertNotIn('\nDetails', output)
        self.assertNotIn('Not evaluated', output)

    def test_pipe_summary_adapter(self):
        value = fixture('selection.summary')
        value['data']['tables'].append(['Pipe type distribution', ['Type', 'Stable id', 'Count'], [['Copper', '101', 2]]])
        output = text(presentation.build_presentation(value))
        self.assertIn('Copper: 2', output)

    def test_pipe_connector_adapter(self):
        value = fixture('selection.connectors')
        value['data']['summary'] += ['Physical piping connector count: 4', 'Reciprocally connected physical connector count: 0', 'Unconnected physical connector count: 4', 'Unreadable connector count: 0']
        output = text(presentation.build_presentation(value))
        self.assertLess(output.index('Physical piping connector count: 4'), output.index('Details'))
        self.assertIn('Unconnected physical connector count: 4', output)

    def test_pipe_assignment_adapter_uses_existing_distribution(self):
        model = presentation.build_presentation(fixture())
        output = text(model)
        self.assertIn('ASSIGNED: 2', output)
        self.assertIn('Systems\nHydronic Supply 1: 1\nHydronic Supply 5: 1', output)
        self.assertNotIn('UNASSIGNED: 0', output)  # No inferred absent-state zeros.
        self.assertFalse(model['truncated'])

    def test_qa_adapter_does_not_recalculate_findings(self):
        value = fixture('selection.qa_health')
        value['classification'] = 'PIPING_QA_HEALTH_YELLOW'
        value['data']['summary'] += ['Deterministic issue count: 7', 'Partial check count: 2']
        value['data']['piping_checks'] = [{'check_id': 'PIPING-QA-004', 'issues': 1, 'skipped': 2, 'status': 'ISSUES_FOUND'}]
        model = presentation.build_presentation(value)
        self.assertIn('Deterministic issue count: 7', text(model))
        self.assertIn('PIPING-QA-004', text(model))
        self.assertEqual(next(b for b in model['blocks'] if b['kind'] == 'status')['tone'], 'WarningBrush')

    def test_per_pipe_technical_detail_preserved(self):
        output = text(presentation.build_presentation(fixture()))
        for value in ('Pipe 358677', 'Pipe 353871', 'MEP system id: 358679', 'Consistency: CONSISTENT', 'Contradictions: none', 'Built-in metadata: built in', 'Fallback metadata: fallback'):
            self.assertIn(value, output)

    def test_character_and_block_caps(self):
        value = fixture()
        value['data']['tables'] += [['Huge', ['A', 'B', 'C', 'D'], [['long value' * 100] * 4 for _ in range(200)]]]
        model = presentation.build_presentation(value)
        self.assertLessEqual(model['character_count'], 16000)
        self.assertLessEqual(len(model['blocks']), presentation.MAX_BLOCKS)
        self.assertTrue(model['truncated'])

    def test_truncation_notice_explicit(self):
        value = fixture()
        value['data']['tables'] += [['Many', ['A'], [[n] for n in range(2000)]]]
        model = presentation.build_presentation(value)
        self.assertIn(presentation.NOTICE, text(model))

    def test_warning_overflow_never_silent(self):
        value = fixture()
        value['data']['warnings'] = ['warning ' * 900] * 20
        model = presentation.build_presentation(value)
        self.assertIn(presentation.WARNING_NOTICE, text(model))
        self.assertIn('PIPING_SYSTEM_ASSIGNMENT_OK', text(model))
        self.assertLessEqual(model['character_count'], 16000)
        self.assertLessEqual(len(model['blocks']), presentation.MAX_BLOCKS)

    def test_unsupported_scalar_payload_tolerated(self):
        for value in (None, 7, 'unrecognized result', ['unrecognized']):
            self.assertIn('Unsupported presentation payload', text(presentation.build_presentation(value)))

    def test_raw_object_rejected_without_repr(self):
        class Raw:
            def __str__(self):
                raise AssertionError()
        self.assertIn('Invalid presentation payload', text(presentation.build_presentation(Raw())))

    def test_dark_resources_exist(self):
        for block in presentation.build_presentation(fixture())['blocks']:
            self.assertIn(block['tone'], theme.PALETTES['dark'])

    def test_light_resources_exist(self):
        for block in presentation.build_presentation(fixture())['blocks']:
            self.assertIn(block['tone'], theme.PALETTES['light'])

    def test_domain_input_unchanged(self):
        value = fixture()
        original = copy.deepcopy(value)
        presentation.build_presentation(value)
        self.assertEqual(value, original)

    def test_no_routing_api_or_mutation_dependencies(self):
        for filename in ('result_presentation.py', 'rich_result.py'):
            tree = ast.parse((ROOT / 'AI.extension/lib/bimcode_ai_pane' / filename).read_text())
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
            self.assertFalse(names & {'execute_headless_modelmind_readonly', 'resolve_headless_modelmind_specialty', 'Document', 'Transaction', 'requests', 'openai'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
