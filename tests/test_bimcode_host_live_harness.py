"""Temporary scalar-only harness; authoritative contracts live in PaneSession."""
import ast
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace as N
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'AI.extension/lib'))
PATH=ROOT/'AI.extension/AI.tab/Dev.panel/M4BHostTest.pushbutton/script.py'


class Harness(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('host_live_harness',PATH)
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        self.output=Mock();self.forms=Mock()
        self.forms.ask_for_string.return_value='M4B_HOST_WRITE_01'
        self.session=N(write_gate=N(permission=N(view_model=lambda:dict(enabled=True)),
                                   admission=N(active=None,safety_locked=False,busy=None)),
            begin_controlled_write_request=Mock(return_value=json.dumps(dict(accepted=True,host_request_id='host'))),
            confirm_controlled_write_request=Mock(return_value='{}'),
            inspect_controlled_write_request=Mock(return_value='{"permission_enabled":true,"busy":false}'))
        for name,value in [('capture_preview_context',dict(fingerprint='snapshot')),('resolve_target',None)]:
            p=patch.object(self.m,name,return_value=value);setattr(self,name,p.start());self.addCleanup(p.stop)

    def run_new(self):
        return self.m.new_request(self.session,'uiapp',self.forms,self.output,'DB')

    def test_no_coordination_imports(self):
        tree=ast.parse(PATH.read_text())
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertFalse(imports & {'bimcode_ai_pane.provider_write_dispatch',
            'bimcode_ai_pane.provider_write_host_bridge','bimcode_ai_pane.provider_write',
            'bimcode_ai_pane.write_leases','bimcode_ai_pane.write_access'})

    def test_actual_session_scalar_path(self):
        self.run_new()
        self.session.begin_controlled_write_request.assert_called_once_with('M4B_HOST_WRITE_01')
        self.session.confirm_controlled_write_request.assert_called_once_with('host')

    def test_missing_inspection_api_stops_before_new_request(self):
        del self.session.inspect_controlled_write_request
        self.forms.CommandSwitchWindow.show.return_value=self.m.NEW
        pyrevit=N(HOST_APP=N(uiapp=None),DB=None,forms=self.forms,script=N(get_output=lambda:self.output))
        with patch.dict(sys.modules,{'pyrevit':pyrevit,'pyrevit.coreutils':N(envvars=N(get_pyrevit_env_var=lambda k:self.session))}):
            with self.assertRaises(AttributeError):
                self.m.main()
        self.assertIn('HARNESS_ERROR',self.output.print_html.call_args[0][0])
        self.session.begin_controlled_write_request.assert_not_called()
        self.session.confirm_controlled_write_request.assert_not_called()
        self.forms.ask_for_string.assert_not_called()
        self.capture_preview_context.assert_not_called()

    def test_permission_disabled(self):
        self.session.inspect_controlled_write_request.return_value='{"permission_enabled":false,"busy":false}'
        self.assertEqual(self.run_new()['reason'],'PERMISSION_DISABLED')
        self.session.begin_controlled_write_request.assert_not_called()

    def test_competing_owner(self):
        self.session.inspect_controlled_write_request.return_value='{"permission_enabled":true,"busy":true}'
        self.assertEqual(self.run_new()['reason'],'EXECUTION_BUSY')
        self.session.begin_controlled_write_request.assert_not_called()

    def test_input_cancel(self):
        self.forms.ask_for_string.return_value=None
        self.assertEqual(self.run_new()['reason'],'INPUT_CANCELLED')
        self.session.begin_controlled_write_request.assert_not_called()

    def test_strict_value(self):
        for value in ('',' bad','bad/','X'*65):
            self.forms.ask_for_string.return_value=value
            self.assertEqual(self.run_new()['reason'],'INVALID_VALUE')
        self.session.begin_controlled_write_request.assert_not_called()

    def test_selection_required(self):
        from bimcode_write_runtime import PreviewBlocked
        self.resolve_target.side_effect=PreviewBlocked('MULTIPLE_ELEMENTS_SELECTED')
        self.assertEqual(self.run_new()['reason'],'MULTIPLE_ELEMENTS_SELECTED')
        self.forms.ask_for_string.assert_not_called()

    def test_stale_input_context(self):
        self.capture_preview_context.side_effect=[dict(fingerprint='a'),dict(fingerprint='b')]
        self.assertEqual(self.run_new()['reason'],'STALE_CONTEXT')
        self.session.begin_controlled_write_request.assert_not_called()

    def test_preview_rejection_never_confirms(self):
        self.session.begin_controlled_write_request.return_value='{"accepted":false,"reason":"REJECTED"}'
        self.run_new()
        self.session.confirm_controlled_write_request.assert_not_called()

    def test_inspection_readonly_ast(self):
        tree=ast.parse(PATH.read_text())
        inspect=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inspect')
        calls={n.func.id if isinstance(n.func,ast.Name) else n.func.attr for n in ast.walk(inspect)
               if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))}
        self.assertEqual(calls,{'display','loads','inspect_controlled_write_request'})

    def test_no_mutation_or_arbitrary_inputs(self):
        tree=ast.parse(PATH.read_text())
        names={n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
        self.assertFalse(names & {'Transaction','Set','Raise','execute','Show','freeze','send_write_explanation'})
        self.assertEqual(PATH.read_text().count('ask_for_string('),1)

    def test_registry_catalog(self):
        from bimcode_ai_pane.ai_tool_registry import TOOLS
        from bimcode_ai_pane.controlled_write_registry import metadata
        self.assertEqual(len(TOOLS),13);self.assertEqual(len(metadata()),1)
        self.assertFalse(metadata()[0]['provider_exposure_allowed'])
        self.assertEqual(len(json.loads((ROOT/'AI.extension/lib/prompt_catalog.json').read_text())),237)

    def test_inspection_preserves_receipt_and_escapes_html(self):
        receipt=json.dumps(dict(state='HOST_RESULT_READY',host_result=dict(reason_code='COMPLETE',before_value='<script>')))
        self.session.inspect_controlled_write_request.return_value=receipt
        self.assertEqual(self.m.inspect(self.session,self.output),json.loads(receipt))
        self.assertNotIn('<script>',self.output.print_html.call_args[0][0])
        self.session.begin_controlled_write_request.assert_not_called()

    def test_inspection_mode_without_permission_or_document(self):
        self.forms.CommandSwitchWindow.show.return_value=self.m.INSPECT
        pyrevit=N(HOST_APP=N(uiapp=None),DB=None,forms=self.forms,script=N(get_output=lambda:self.output))
        self.session.write_gate.permission.view_model=lambda:dict(enabled=False)
        with patch.dict(sys.modules,{'pyrevit':pyrevit,'pyrevit.coreutils':N(envvars=N(get_pyrevit_env_var=lambda k:self.session))}):
            self.m.main()
        self.session.inspect_controlled_write_request.assert_called_once_with()
        self.session.begin_controlled_write_request.assert_not_called()
