"""Session-owned entry guards; real cross-engine runtime probe is the .ps1 test."""
import ast
import json
from pathlib import Path
import sys
from types import SimpleNamespace as N
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'AI.extension/lib'))
from bimcode_ai_pane import provider_write_session as boundary
from bimcode_ai_pane.write_access import OperationAdmission
from bimcode_ai_pane.session_write_gate import SessionWriteGate


class SessionBoundary(unittest.TestCase):
    def setUp(self):
        self.session=N(write_gate=SessionWriteGate(OperationAdmission()),disposed=False)
        self.api=boundary.SessionWrites(self.session)

    def test_disabled_no_bridge(self):
        with patch.object(boundary,'get_bridge') as bridge:
            self.assertEqual(json.loads(self.api.begin('Value'))['reason'],'PERMISSION_DISABLED')
            bridge.assert_not_called()

    def test_invalid_value_no_bridge(self):
        with patch.object(boundary,'get_bridge') as bridge:
            self.assertEqual(json.loads(self.api.begin(' bad'))['reason'],'INVALID_VALUE')
            bridge.assert_not_called()

    def test_inspect_is_scalar_and_does_not_create_bridge(self):
        with patch.object(boundary,'get_bridge') as bridge:
            self.assertEqual(json.loads(self.api.inspect())['reason'],'NO_RETAINED_HARNESS_REQUEST')
            bridge.assert_not_called()

    def test_unknown_confirmation_no_bridge(self):
        with patch.object(boundary,'get_bridge') as bridge:
            self.assertEqual(json.loads(self.api.confirm('unknown'))['reason'],'CORRELATION_MISMATCH')
            bridge.assert_not_called()

    def test_authority_injection_rejected(self):
        for field in ('owner','token','call_id','response_id','logical_request_id','target','guid','action'):
            with self.assertRaises(TypeError):self.api.begin('Value',**{field:'forged'})
        with self.assertRaises(TypeError):self.api.confirm('host',confirmed=True)

    def test_session_constructs_and_delegates_in_own_module(self):
        path=Path(__file__).resolve().parents[1]/'AI.extension/lib/bimcode_ai_pane/lifecycle.py'
        tree=ast.parse(path.read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PaneSession')
        functions={n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='SessionWrites'
                            for n in ast.walk(functions['__init__'])))
        for method,target in [('begin_controlled_write_request','begin'),('confirm_controlled_write_request','confirm'),
                              ('inspect_controlled_write_request','inspect')]:
            returned=functions[method].body[0].value
            self.assertEqual(returned.func.attr,target)
            self.assertEqual(returned.func.value.attr,'controlled_writes')
