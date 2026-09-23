"""M2A offline tests. python -B tests/test_modelmind_headless.py

CPython sanitizes CLR enum '.None' syntax ONLY in test compilation, never on
disk or in the production loader. Host stubs cannot prove live Revit behavior.
"""
import ast
import builtins
import gc
import json
import pathlib
import re
import subprocess
import sys
import types
import unittest
import weakref
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py'
BASELINE = 'd25c545e0e4f92d14492f52f04d109bd32f15beb'
sys.path.insert(0, str(ROOT / 'AI.extension/lib'))
import modelmind_headless as seam


def sanitized(source):
    if isinstance(source, bytes):
        source = source.decode('utf-8-sig')
    return re.sub(r'\.None\b', '._None', source)


class Doc:
    IsValidObject = True
    Title = 'Offline fixture'
    ActiveView = types.SimpleNamespace(Name='View', ViewType='ThreeD')

    def Equals(self, other):
        return self is other


def context():
    document = Doc()
    return document, types.SimpleNamespace(
        Document=document, ActiveView=document.ActiveView,
        Selection=types.SimpleNamespace(GetElementIds=lambda: []))


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.previous = seam._MODULE
        seam._MODULE = None
        self.imports = []
        self.original_import = builtins.__import__
        self.original_compile = builtins.compile
        self.host = types.ModuleType('pyrevit')
        self.host.DB = types.SimpleNamespace()

        def import_guard(name, *args, **kwargs):
            self.imports.append(name)
            if name == 'pyrevit':
                # NO forms, revit, script, settings, agent or provider stubs.
                return self.host
            if name in ('requests', 'subprocess', 'System', 'clr', 'ModelService') or name.startswith('ai_'):
                raise AssertionError('Forbidden headless import: ' + name)
            return self.original_import(name, *args, **kwargs)

        def compile_source(source, path, mode, *args, **kwargs):
            return self.original_compile(sanitized(source), path, mode, *args, **kwargs)

        self.import_patch = patch('builtins.__import__', import_guard)
        self.compile_patch = patch.object(seam, 'compile', compile_source, create=True)
        self.import_patch.start()
        self.compile_patch.start()

    def tearDown(self):
        self.compile_patch.stop()
        self.import_patch.stop()
        seam._MODULE = self.previous

    def test_bootstrap_without_ui_provider_agent_or_document_capture(self):
        module = seam._load_backend()
        self.assertEqual(module.OllamaAIChat.__bases__, (object,))
        self.assertEqual(vars(object.__new__(module.OllamaAIChat)), {})
        self.assertIsNone(module.doc)
        self.assertIsNone(module.uidoc)
        self.assertFalse(hasattr(module, 'forms'))
        self.assertFalse(hasattr(module, 'AgentSession'))
        self.assertFalse(hasattr(module, 'requests'))

    def test_import_is_cached_and_does_not_change_global_import_state(self):
        paths = list(sys.path)
        modules = dict(sys.modules)
        first = seam._load_backend()
        self.assertIs(first, seam._load_backend())
        self.assertEqual(paths, sys.path)
        self.assertNotIn(first.__name__, sys.modules)
        self.assertNotIn('_MODELMIND_HEADLESS_BOOTSTRAP', globals())
        for name in ('ModelService', 'ai_agent_session', 'ai_local_store'):
            self.assertIs(sys.modules.get(name), modules.get(name))

    def test_alert_untouched(self):
        alert = object()
        self.host.forms = types.SimpleNamespace(alert=alert)
        seam._load_backend()
        self.assertIs(self.host.forms.alert, alert)

    def test_all_twelve_real_builders_empty_selection(self):
        for action in seam.SUPPORTED_ACTIONS:
            with self.subTest(action=action):
                result = seam.execute_headless_modelmind_readonly(action, *context())
                self.assertTrue(result['ok'], result)
                self.assertEqual(result['action_id'], action)
                self.assertTrue(result['classification'].endswith('_NOT_READY'))
                self.assertEqual(result['reason_code'], 'NO_ELEMENTS_SELECTED')
                json.dumps(result, allow_nan=False)
                self.assertIsNone(seam._MODULE.doc)
                self.assertIsNone(seam._MODULE.uidoc)

    def test_actual_builder_invocation_context_and_raw_record_omission(self):
        module = seam._load_backend()
        document, uidocument = context()
        calls = []

        def builder(worker, prompt, action_key):
            calls.append((prompt, action_key))
            self.assertIs(module.doc, document)
            self.assertIs(module.uidoc, uidocument)
            self.assertEqual(vars(worker), {})
            return {'classification': 'UNCHANGED', 'summary': ['Original'],
                    'warnings': ['Original warning'], 'pipe_records': [document]}

        with patch.object(module.OllamaAIChat, '_piping_ro_001_build_data', builder):
            result = seam.execute_headless_modelmind_readonly('PIPING-RO-001-A01', document, uidocument)
        self.assertEqual(calls, [('show selected pipes summary', 'pipes_summary')])
        self.assertEqual(result['classification'], 'UNCHANGED')
        self.assertEqual(result['warnings'], ['Original warning'])
        self.assertNotIn('pipe_records', result)
        self.assertIsNone(module.doc)
        self.assertIsNone(module.uidoc)

    def test_real_builders_with_supported_and_unsupported_minimal_elements(self):
        # Incomplete host fakes exercise real record/QA/error paths, not live
        # semantics. No builder/helper replacement and no UI/agent instance.
        class ElementId:
            def __init__(self, value):
                self.IntegerValue = value
                self.Value = value

            def __str__(self):
                return str(self.IntegerValue)

        class Element:
            IsPlaceholder = False
            Name = 'Offline element'
            UniqueId = 'offline-id'
            Parameters = []

            def GetTypeId(self):
                return ElementId(-1)

            def get_Parameter(self, unused):
                return None

            def LookupParameter(self, unused):
                return None

        class Pipe(Element):
            pass

        class Duct(Element):
            pass

        categories = sorted(set(re.findall(r'OST_\w+', SCRIPT.read_text(encoding='utf-8-sig'))))
        enum = types.SimpleNamespace(**{name: -(index + 1) for index, name in enumerate(categories)})
        self.host.DB = types.SimpleNamespace(
            BuiltInCategory=enum, ElementId=ElementId,
            Plumbing=types.SimpleNamespace(Pipe=Pipe),
            Mechanical=types.SimpleNamespace(Duct=Duct))
        module = seam._load_backend()
        fixtures = [('PIPING', Pipe, 'OST_PipeCurves'), ('HVAC', Duct, 'OST_DuctCurves'),
                    ('ELECTRICAL', Element, 'OST_LightingFixtures'),
                    ('ELECTRICAL', Element, 'OST_ElectricalEquipment')]
        for specialty, cls, category in fixtures:
            for supported in (True, False):
                element = cls() if supported else Element()
                element.Id = ElementId(123)
                element.Category = types.SimpleNamespace(
                    Id=ElementId(getattr(enum, category) if supported else -999999), Name=category)
                document, uidocument = context()
                document.GetElement = lambda unused: element
                uidocument.Selection.GetElementIds = lambda: [element.Id]
                scope = seam.resolve_headless_modelmind_specialty(document, uidocument)
                self.assertTrue(scope['ok'], scope)
                self.assertEqual(scope['specialties'], [specialty] if supported else [])
                self.assertEqual(scope['unsupported_count'], 0 if supported else 1)
                self.assertIsNone(module.doc)
                self.assertIsNone(module.uidoc)
                for number in range(1, 5):
                    action = '{}-RO-001-A{:02d}'.format(specialty, number)
                    with self.subTest(action=action, category=category, supported=supported):
                        result = seam.execute_headless_modelmind_readonly(action, document, uidocument)
                        self.assertTrue(result['ok'], result)
                        self.assertEqual(result['selected_reference_count'], 1)
                        self.assertTrue(result['tables'])
                        if not supported:
                            self.assertTrue(result['classification'].endswith('_NOT_READY'))
                        json.dumps(result, allow_nan=False)
                        self.assertIsNone(module.doc)

    def test_exception_restores_context_and_next_request_works(self):
        module = seam._load_backend()
        with patch.object(module.OllamaAIChat, '_piping_ro_001_build_data', side_effect=RuntimeError('private')):
            result = seam.execute_headless_modelmind_readonly('PIPING-RO-001-A01', *context())
        self.assertEqual(result['error_code'], 'HEADLESS_EXECUTION_FAILED')
        self.assertNotIn('private', str(result))
        self.assertIsNone(module.doc)
        self.assertIsNone(module.uidoc)
        self.assertTrue(seam.execute_headless_modelmind_readonly('PIPING-RO-001-A01', *context())['ok'])

    def test_projection_failure_restores_context(self):
        module = seam._load_backend()
        with patch.object(module.OllamaAIChat, '_piping_ro_001_build_data', return_value={'summary': [Doc()]}):
            result = seam.execute_headless_modelmind_readonly('PIPING-RO-001-A01', *context())
        self.assertEqual(result['error_code'], 'RESULT_PROJECTION_FAILED')
        self.assertIsNone(module.doc)
        self.assertIsNone(module.uidoc)

    def test_no_document_retained(self):
        document, uidocument = context()
        reference = weakref.ref(document)
        result = seam.execute_headless_modelmind_readonly('HVAC-RO-001-A01', document, uidocument)
        self.assertTrue(result['ok'])
        del document, uidocument
        gc.collect()
        self.assertIsNone(reference())

    def test_nested_execution_rejected(self):
        module = seam._load_backend()
        document, uidocument = context()

        def builder(worker, prompt, action):
            nested = seam.execute_headless_modelmind_readonly('HVAC-RO-001-A01', document, uidocument)
            self.assertEqual(nested['error_code'], 'EXECUTION_BUSY')
            self.assertIs(module.doc, document)
            return {'summary': []}

        with patch.object(module.OllamaAIChat, '_piping_ro_001_build_data', builder):
            self.assertTrue(seam.execute_headless_modelmind_readonly('PIPING-RO-001-A01', document, uidocument)['ok'])

    def test_invalid_or_mismatched_document_rejected_before_import(self):
        document, uidocument = context()
        for doc in (None, Doc()):
            result = seam.execute_headless_modelmind_readonly('PIPING-RO-001-A01', doc, uidocument)
            self.assertEqual(result['error_code'], 'INVALID_DOCUMENT_CONTEXT')
        document.IsValidObject = False
        self.assertEqual(seam.execute_headless_modelmind_readonly('PIPING-RO-001-A01', document, uidocument)['error_code'], 'INVALID_DOCUMENT_CONTEXT')
        self.assertIsNone(seam._MODULE)


class ProjectionAndGuardTests(unittest.TestCase):
    def test_scalar_types(self):
        values = [True, False, None, 7, -9, 1.25, 'id:353871']
        self.assertEqual(seam.project_value(values), values)

    def test_recursive_containers_preserve_order(self):
        self.assertEqual(seam.project_value({'rows': [('b', 2), ('a', 1)]}), {'rows': [['b', 2], ['a', 1]]})

    def test_raw_objects_callables_and_element_ids_rejected_without_stringification(self):
        class Raw:
            def __str__(self):
                raise AssertionError('Must not stringify')
        for value in (Raw(), Doc(), lambda: None, {1, 2}, types.SimpleNamespace(Value=353871), {1: 'bad key'}):
            with self.assertRaises(seam.ProjectionError):
                seam.project_value(value)

    def test_scalar_element_ids_need_no_api_conversion(self):
        self.assertEqual(seam.project_value({'element_id': '353871'}), {'element_id': '353871'})

    def test_bounds_cycles_and_nonfinite_numbers_fail_explicitly(self):
        cycle = []
        cycle.append(cycle)
        for value in (cycle, [0] * 100001, 'x' * 8193, float('nan'), float('inf'), 2 ** 100):
            with self.assertRaises(seam.ProjectionError):
                seam.project_value(value)

    def test_context_restores_previous_values_on_success_and_failure(self):
        module = types.SimpleNamespace(doc=object(), uidoc=object())
        previous = module.doc, module.uidoc
        for fail in (False, True):
            try:
                with seam._document_context(module, 'new doc', 'new uidoc'):
                    self.assertEqual((module.doc, module.uidoc), ('new doc', 'new uidoc'))
                    if fail:
                        raise RuntimeError()
            except RuntimeError:
                pass
            self.assertEqual((module.doc, module.uidoc), previous)

    def test_overlapping_call_rejected_without_document_access(self):
        seam._EXECUTION_LOCK.acquire()
        try:
            self.assertEqual(seam.execute_headless_modelmind_readonly('PIPING-RO-001-A01', object(), object())['error_code'], 'EXECUTION_BUSY')
        finally:
            seam._EXECUTION_LOCK.release()

    def test_unknown_actions_rejected(self):
        for action in ('export', 'qa_health', 'PIPING-RO-001-A05', object()):
            self.assertEqual(seam.execute_headless_modelmind_readonly(action, None, None)['error_code'], 'UNSUPPORTED_ACTION')


class RegressionTests(unittest.TestCase):
    def reconstructed(self):
        import copy
        tree = copy.deepcopy(self.current)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'OllamaAIChat')
        methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
        for specialty in ('piping', 'hvac', 'electrical'):
            name = '_' + specialty + '_ro_001_build_data'
            core_name = '_' + specialty + '_ro_001_build_from_snapshot'
            wrapper, core = methods[name], methods[core_name]
            expected = ast.parse('def '+name+'(self, prompt, action_key):\n    snapshot = self._mep_ro_001_selection_snapshot()\n    return self.'+core_name+'(prompt, action_key, snapshot)').body[0]
            self.assertEqual(ast.dump(wrapper), ast.dump(expected))
            self.assertEqual([a.arg for a in core.args.args], ['self', 'prompt', 'action_key', 'snapshot'])
            wrapper.body = wrapper.body[:1] + core.body
            cls.body.remove(core)
        return tree

    @classmethod
    def setUpClass(cls):
        cls.current = ast.parse(sanitized(SCRIPT.read_bytes()))
        cls.baseline = ast.parse(sanitized(subprocess.check_output([
            'git', 'show', BASELINE + ':' + SCRIPT.relative_to(ROOT).as_posix()])))

    def test_every_existing_function_ast_unchanged(self):
        def functions(tree):
            return [ast.dump(n, include_attributes=False) for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        self.assertEqual(functions(self.baseline), functions(self.reconstructed()))

    def test_builders_have_no_uninitialized_instance_fields(self):
        cls = next(n for n in self.current.body if isinstance(n, ast.ClassDef) and n.name == 'OllamaAIChat')
        methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
        pending = [spec[2] for spec in seam._SPECS]
        visited = set()
        while pending:
            name = pending.pop()
            if name in visited:
                continue
            visited.add(name)
            for node in ast.walk(methods[name]):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
                    self.assertIn(node.attr, methods, (name, node.attr))
                    self.assertIsInstance(node.ctx, ast.Load)
                    pending.append(node.attr)
        self.assertEqual(len(visited), 105)  # Three snapshot-fed cores; same closure.

    def test_normal_bootstrap_ast_is_baseline_when_guard_is_false(self):
        class NormalMode(ast.NodeTransformer):
            def visit_Assign(self, node):
                if any(isinstance(t, ast.Name) and t.id == '_MODELMIND_HEADLESS' for t in node.targets):
                    return None
                return self.generic_visit(node)

            def visit_Name(self, node):
                return ast.Constant(False) if node.id == '_MODELMIND_HEADLESS' else node

            def visit_UnaryOp(self, node):
                node = self.generic_visit(node)
                if isinstance(node.op, ast.Not) and isinstance(node.operand, ast.Constant):
                    return ast.Constant(not node.operand.value)
                return node

            def visit_BoolOp(self, node):
                node = self.generic_visit(node)
                if isinstance(node.op, ast.And) and isinstance(node.values[0], ast.Constant) and node.values[0].value is True:
                    return node.values[1]
                return node

            def visit_If(self, node):
                node = self.generic_visit(node)
                if isinstance(node.test, ast.Constant):
                    return node.body if node.test.value else node.orelse
                return node

            def visit_IfExp(self, node):
                node = self.generic_visit(node)
                return (node.body if node.test.value else node.orelse) if isinstance(node.test, ast.Constant) else node

        import copy
        normal = NormalMode().visit(self.reconstructed())
        self.assertEqual(ast.dump(normal), ast.dump(self.baseline))

    def test_default_guard_is_explicit_and_false(self):
        assignment = next(n for n in self.current.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_MODELMIND_HEADLESS' for t in n.targets))
        expression = compile(ast.Expression(assignment.value), '<flag>', 'eval')
        self.assertFalse(eval(expression, {}))
        self.assertTrue(eval(expression, {'_MODELMIND_HEADLESS_BOOTSTRAP': True}))
        self.assertFalse(eval(expression, {'_MODELMIND_HEADLESS_BOOTSTRAP': 'true'}))

    def test_complete_builder_closure_has_no_suppressed_or_mutating_dependencies(self):
        cls = next(n for n in self.current.body if isinstance(n, ast.ClassDef) and n.name == 'OllamaAIChat')
        methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
        functions = {n.name: n for n in self.current.body if isinstance(n, ast.FunctionDef)}
        nodes = dict(functions, **methods)
        pending = [spec[2] for spec in seam._SPECS]
        visited = set()
        forbidden = {'forms', 'revit', 'requests', 'subprocess', 'logger', 'pyscript',
                     'System', 'script', 'AgentSession', 'ModelService', 'clr'}
        forbidden_attributes = {'Transaction', 'TransactionGroup', 'Set', 'Delete',
                                'SetElementIds', 'PickObject', 'PostCommand', 'ShowDialog'}
        while pending:
            name = pending.pop()
            if name in visited:
                continue
            visited.add(name)
            for node in ast.walk(nodes[name]):
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, forbidden, name)
                    if node.id in functions:
                        pending.append(node.id)
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, forbidden_attributes, name)
                    if isinstance(node.value, ast.Name) and node.value.id == 'self':
                        pending.append(node.attr)
        self.assertEqual(len(visited), 122)  # Three snapshot-fed cores.

    def test_catalog_unchanged_and_237(self):
        path = 'AI.extension/lib/prompt_catalog.json'
        baseline = subprocess.check_output(['git', 'show', BASELINE + ':' + path])
        current = (ROOT / path).read_bytes().replace(b'\r\n', b'\n')
        self.assertEqual(current, baseline)
        self.assertEqual(len(json.loads(current)), 237)

    def test_facade_no_mutation_network_or_provider_calls(self):
        tree = ast.parse(pathlib.Path(seam.__file__).read_text())
        forbidden = {'Transaction', 'TransactionGroup', 'Set', 'Delete', 'Create', 'SetElementIds', 'PickObject', 'PostCommand', 'ShowDialog', 'urlopen', 'requests', 'OpenAI'}
        names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        self.assertFalse(names & forbidden)
        imports = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
        self.assertFalse(imports & {'requests', 'subprocess', 'ModelService', 'forms', 'revit'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
