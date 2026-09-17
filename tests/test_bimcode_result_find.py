"""M2-UI-03: local, bounded presentation search; no Revit required."""
import ast
import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'AI.extension/lib'))
from bimcode_ai_pane.result_find import ResultFind, fragments
from bimcode_ai_pane.rich_result import block_style
from bimcode_ai_pane.result_presentation import build_presentation
from bimcode_ai_pane.theme import PALETTES
from test_bimcode_rich_result import fixture


class FindTests(unittest.TestCase):
    def setUp(self):
        self.model = build_presentation(fixture())
        self.find = ResultFind()

    def test_case_insensitive_literal_substring(self):
        self.find.search(self.model, 'hydronic')
        expected = self.find.matches[:]
        self.find.search(self.model, 'hYdRoNiC')
        self.assertEqual(expected, self.find.matches)
        self.assertTrue(expected)
        self.find.search(self.model, '.*')
        self.assertEqual(self.find.matches, [])

    def test_navigation_wraps_both_directions(self):
        self.find.search(self.model, 'Hydronic')
        self.find.move(-1)
        self.assertEqual(self.find.current, len(self.find.matches) - 1)
        self.find.move(1)
        self.assertEqual(self.find.current, 0)
        self.find.move(1)
        self.assertEqual(self.find.current, 1)

    def test_empty_no_match_and_reset(self):
        for model, query in (({'blocks': []}, 'a'), (self.model, ''), (self.model, 'nonexistentxyz')):
            self.find.search(model, query)
            self.find.move(1)
            self.find.move(-1)
            self.assertEqual(self.find.caption(), '0/0')

    def test_search_preserves_every_displayed_character_and_payload(self):
        original = copy.deepcopy(self.model)
        self.find.search(self.model, 'system')
        for index, block in enumerate(self.model['blocks']):
            matches = [(n, s, e) for n, (i, s, e) in enumerate(self.find.matches) if i == index]
            for text, offset in ((block['label'], 0), (block['text'], len(block['label']))):
                runs = list(fragments(text, offset, matches, self.find.current))
                self.assertEqual(''.join(t for t, brush in runs), text)
                for unused, brush in runs:
                    if brush:
                        for palette in PALETTES.values():
                            self.assertIn(brush, palette)
        self.assertEqual(original, self.model)

    def test_cross_label_value_match_highlights_both_without_duplication(self):
        matches = [(0, 2, 7)]
        self.assertEqual(list(fragments('abc', 0, matches, 0)), [('ab', None), ('c', 'AccentBrush')])
        self.assertEqual(list(fragments('defgh', 3, matches, 0)), [('defg', 'AccentBrush'), ('h', None)])

    def test_section_and_detail_styles(self):
        self.assertTrue(block_style('heading')['separator'])
        self.assertGreaterEqual(block_style('heading')['top'], 18)
        self.assertTrue(block_style('record', True)['separator'])
        self.assertGreater(block_style('technical', True)['indent'], 0)
        self.assertEqual(block_style('technical', False)['indent'], 0)

    def test_dense_adjacent_matches_coalesce_without_losing_navigation(self):
        self.find.search({'blocks': [dict(label='', text='a' * 15900)]}, 'a')
        self.assertEqual(len(self.find.matches), 15900)
        matches = [(n, s, e) for n, (i, s, e) in enumerate(self.find.matches)]
        self.assertEqual(len(list(fragments('a' * 15900, 0, matches, 0))), 2)
        self.find.move(7900)
        self.assertEqual(len(list(fragments('a' * 15900, 0, matches, self.find.current))), 3)

    def test_find_callbacks_cannot_dispatch_or_refresh(self):
        source = (ROOT / 'AI.extension/lib/bimcode_ai_pane/panel.py').read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and ('find' in node.name):
                names = {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}
                self.assertFalse(names & {'_request_tool', '_request_refresh', 'Raise', 'execute', 'render', 'Selection'})
        for filename in ('result_find.py', 'rich_result.py'):
            tree = ast.parse((ROOT / 'AI.extension/lib/bimcode_ai_pane' / filename).read_text())
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
            self.assertFalse(names & {'Transaction', 'Document', 'requests', 'openai', 'urllib', 'Autodesk'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
