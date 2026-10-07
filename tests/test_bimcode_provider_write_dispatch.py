"""Internal preview-only dispatch; real domain contracts with fake Revit DB."""
import ast
import json
from pathlib import Path
import sys
from types import SimpleNamespace as N
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'AI.extension/lib'))
from bimcode_ai_pane import provider_write as machine
from bimcode_ai_pane import provider_write_dispatch as dispatch
from bimcode_ai_pane.write_access import admission_for, owner_document_key
from bimcode_ai_pane.session_write_gate import SessionWriteGate, read_document
from bimcode_ai_pane.write_clock import Clock
from bimcode_ai_pane.controlled_write_registry import metadata
from bimcode_ai_pane.ai_tool_registry import TOOLS
from test_bimcode_write_runtime import fixture, Identity


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture()
        self.f.doc.PathName = ''
        self.f.doc.IsLinked = False
        self.f.db.Transaction = Mock(side_effect=AssertionError('No transaction allowed'))
        self.f.parameter.Set = Mock(side_effect=AssertionError('No Set allowed'))
        self.session = N(document_identity=(123, 'Fixture', ''), context_generation=0,
            selection_generation=0, m4a_write=N(epoch=0), tools=N(pending=None), ai=N(turn=None))
        self.gate = self.session.write_gate = SessionWriteGate(admission_for(self.session))
        document, facts = read_document(self.f.app, self.f.db, self.f.guid)
        self.assertEqual(document, owner_document_key(self.session))
        self.gate.observe(document, facts)
        self.gate.permission.enable_from_human(document, facts, True)
        self.now = 10.0
        self.clock = Clock(lambda: self.now, lambda: '2026-10-07T12:00:00Z')
        self.identity = machine.correlation('logical1', 'host1', str(id(self.session)), document,
                                             'response1', 'call1', 'Value_01')
        self.d = self.make()
        self.call = dict(name='set_selected_pipe_test_text', call_id='call1', arguments={'value':'Value_01'})

    def make(self, identity=None, ready=True):
        return dispatch.Dispatcher(self.session, identity or self.identity, self.clock, ready)

    def run_dispatch(self, d=None):
        d = d or self.d
        return d._dispatch(self.f.app, self.call, d.identity.previous_response_id, self.f.db, self.f.guid)

    def check(self, identity=None):
        return self.d._check_preview(self.f.app, identity or self.identity, self.f.db, self.f.guid)

    def tearDown(self):
        self.f.db.Transaction.assert_not_called()
        self.f.parameter.Set.assert_not_called()

    def reject(self, reason, d=None):
        outcome = self.run_dispatch(d)
        self.assertFalse(outcome.accepted)
        self.assertEqual(outcome.reason, reason)
        self.assertEqual(outcome.request.state, 'COMPLETED')
        self.assertFalse(json.loads(outcome.request.host_result.json)['model_modified'])
        return outcome

    def test_disabled_no_preview(self):
        self.gate.permission.disable()
        with patch.object(dispatch, '_preview') as build:
            self.reject('PERMISSION_DISABLED')
            build.assert_not_called()

    def test_unknown_readiness_rejected(self):
        self.reject('IMPLEMENTATION_UNAVAILABLE', self.make(ready=None))

    def test_happy_preview_only(self):
        outcome = self.run_dispatch()
        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.request.state, 'AWAITING_HUMAN_CONFIRMATION')
        self.assertEqual(outcome.request.owner, 'CONTROLLED_WRITE_PROVIDER_TOOL')
        self.assertEqual(self.d.owner.owner_type, 'CONTROLLED_WRITE_PROVIDER_TOOL')
        self.assertEqual(self.gate.lifecycle, self.d.lifecycle)
        p = json.loads(outcome.preview_json)
        self.assertEqual(p['parameter_guid'], self.f.guid.Value)
        self.assertEqual(p['proposed_value'], 'Value_01')
        self.assertEqual(p['target_unique_id'], 'pipe-1')
        self.assertFalse(p['model_modified'])
        self.assertFalse(p['transaction_started'])
        self.assertEqual(outcome.lease.expires_at-outcome.lease.created_at, 120)
        self.assertEqual(self.d.leases.queue.state, 'NOT_STARTED')
        with self.assertRaises(AttributeError):
            outcome.request.correlation.value = 'Other'
        self.assertTrue(self.check().accepted)

    def test_invalid_value_before_preview(self):
        self.call['arguments']['value'] = ' invalid '
        with patch.object(dispatch, '_preview') as build:
            self.reject('INVALID_VALUE')
            build.assert_not_called()

    def test_extra_argument_rejected(self):
        self.call['arguments']['target'] = 1
        self.reject('INVALID_ARGUMENTS')

    def test_no_selection(self):
        self.f.uidoc.Selection.GetElementIds = lambda: []
        self.reject('NO_ELEMENTS_SELECTED')

    def test_multiple_selection(self):
        self.f.uidoc.Selection.GetElementIds = lambda: [Identity(1),Identity(2)]
        self.reject('MULTIPLE_ELEMENTS_SELECTED')

    def test_unsupported_target(self):
        self.f.pipe.IsPlaceholder = True
        self.reject('UNSUPPORTED_TARGET')

    def test_workshared(self):
        self.f.doc.IsWorkshared = True
        self.reject('WORKSHARED_DOCUMENT')

    def test_missing_parameter(self):
        self.f.db.SharedParameterElement.Lookup = lambda *args: None
        self.reject('FIXED_PARAMETER_MISSING')

    def test_invalid_binding(self):
        self.f.doc.ParameterBindings.get_Item = lambda d: object()
        self.reject('FIXED_PARAMETER_BINDING_INVALID')

    def test_wrong_storage(self):
        self.f.parameter.StorageType = 'Integer'
        self.reject('STORAGE_TYPE_UNSUPPORTED')

    def test_unknown_document_fact(self):
        del self.f.doc.IsLinked
        self.reject('DOCUMENT_FACTS_UNREADABLE')

    def test_human_owner_conflict(self):
        held = self.d.admission.acquire('HUMAN_DEV_WRITE','x','y',self.identity.document_id,str(id(self.session)),0)
        self.reject('EXECUTION_BUSY')
        self.assertEqual(self.d.admission.active, held)

    def test_provider_owner_conflict(self):
        self.run_dispatch()
        other = self.make(self.identity._replace(logical_request_id='other',host_request_id='other',
                                                previous_response_id='other',call_id='other'))
        self.call['call_id'] = 'other'
        self.reject('EXECUTION_BUSY', other)
        self.assertEqual(self.d.admission.active, self.d.owner)

    def test_safety_lock(self):
        self.d.admission.safety_locked = True
        self.reject('UNRESOLVED_MUTATION_SAFETY')
        self.assertTrue(self.d.admission.safety_locked)

    def test_call_mismatch(self):
        self.call['call_id'] = 'other'
        self.reject('CORRELATION_MISMATCH')

    def test_host_request_mismatch_check(self):
        self.run_dispatch()
        self.assertEqual(self.check(self.identity._replace(host_request_id='other')).reason,'CORRELATION_MISMATCH')
        self.assertEqual(self.d.request.state,'AWAITING_HUMAN_CONFIRMATION')

    def test_value_mismatch(self):
        self.call['arguments']['value'] = 'Other'
        self.reject('CORRELATION_MISMATCH')

    def test_response_mismatch(self):
        out = self.d._dispatch(self.f.app,self.call,'other',self.f.db,self.f.guid)
        self.assertEqual(out.reason,'CORRELATION_MISMATCH')

    def test_session_mismatch(self):
        self.reject('CORRELATION_MISMATCH',self.make(self.identity._replace(session_id='other')))

    def test_expiry_terminal_and_replay(self):
        self.run_dispatch()
        self.now = 130
        out = self.check()
        self.assertEqual(out.reason,'PREVIEW_LEASE_EXPIRED')
        self.assertEqual(out.request.state,'EXPIRED')
        self.assertIsNone(self.d.admission.active)
        self.assertEqual(self.run_dispatch().reason,'REQUEST_TERMINAL')
        self.gate.permission.enable_from_human(self.gate.document,self.gate.facts,True)
        self.reject('REQUEST_TERMINAL', self.make())

    def test_second_call_while_pending(self):
        self.run_dispatch()
        self.assertEqual(self.run_dispatch().reason,'AI_TOOL_LOOP_LIMIT')

    def test_selection_invalidation(self):
        self.run_dispatch()
        self.f.uidoc.Selection.GetElementIds = lambda: []
        self.assertEqual(self.check().reason,'PREVIEW_LEASE_INVALIDATED')
        self.assertIsNone(self.d.admission.active)

    def test_before_value_invalidation(self):
        self.run_dispatch()
        self.f.parameter.AsString = lambda: 'Changed'
        self.assertEqual(self.check().reason,'PREVIEW_LEASE_INVALIDATED')

    def test_model_epoch_invalidation(self):
        self.run_dispatch()
        self.session.m4a_write.epoch += 1
        self.assertEqual(self.check().reason,'PREVIEW_LEASE_INVALIDATED')

    def test_gate_lifecycle_cleanup(self):
        self.run_dispatch()
        self.gate.cleanup('DOCUMENT_CLOSE')
        self.assertIsNone(self.d.admission.active)
        self.assertEqual(self.check().reason,'PREVIEW_LEASE_INVALIDATED')
        self.assertEqual(self.d.request.state,'COMPLETED')

    def test_preview_failure_is_explicit(self):
        self.f.parameter.AsString = Mock(side_effect=RuntimeError('private API data'))
        out = self.reject('READ_FAILED')
        self.assertNotIn('private API data',str(out))

    def test_unexpected_dispatch_error(self):
        with patch.object(dispatch,'_preview',side_effect=RuntimeError('private')):
            self.reject('INTERNAL_DISPATCH_ERROR')
        self.assertIsNone(self.d.admission.active)

    def test_completion_and_continuation_are_not_executed(self):
        self.run_dispatch()
        self.assertIsNone(self.d.sink.receipt)
        self.assertIsNone(self.d.lifecycle.continuation)
        for name in ('confirm','execute','continue_provider'):
            self.assertFalse(hasattr(self.d,name))

    def test_registry_and_refusal_unchanged(self):
        import subprocess
        for path in ('BIMCode_Provider/provider.py','BIMCode_Provider/tool_protocol.py',
                     'AI.extension/lib/bimcode_ai_pane/ai_tool.py',
                     'AI.extension/lib/bimcode_ai_pane/controlled_write_registry.py'):
            self.assertEqual(subprocess.check_output(['git','show','HEAD:'+path]).replace(b'\r\n',b'\n'),
                             (ROOT/path).read_bytes().replace(b'\r\n',b'\n'))
        self.assertEqual(len(TOOLS),13)
        self.assertFalse(metadata()[0]['provider_exposure_allowed'])
        self.assertNotIn('set_selected_pipe_test_text',[row[0] for row in TOOLS])

    def test_no_mutation_or_execution_calls(self):
        tree=ast.parse(Path(dispatch.__file__).read_text())
        attrs=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        for name in ('Transaction','Set','Raise','confirm','execute','send_write_explanation'):
            self.assertNotIn(name,attrs)

    def test_terminal_rejection_cannot_be_retried_in_new_dispatcher(self):
        self.gate.permission.disable()
        self.reject('PERMISSION_DISABLED')
        self.gate.permission.enable_from_human(self.gate.document,self.gate.facts,True)
        self.reject('REQUEST_TERMINAL',self.make())

    def test_second_call_from_same_provider_response_rejected(self):
        self.run_dispatch()
        other = self.make(self.identity._replace(logical_request_id='other',host_request_id='other',call_id='other'))
        self.call['call_id']='other'
        self.reject('REQUEST_TERMINAL',other)

    def test_direct_permission_revocation(self):
        self.run_dispatch()
        self.gate.permission.disable()
        self.assertEqual(self.check().reason,'PREVIEW_LEASE_INVALIDATED')
        self.assertIsNone(self.d.admission.active)

    def test_late_check_does_not_replace_newer_gate_request(self):
        self.run_dispatch()
        self.gate.cleanup('ABANDONED')
        sentinel=object()
        self.gate.lifecycle=sentinel
        self.gate.request=sentinel
        self.assertEqual(self.check().reason,'PREVIEW_LEASE_INVALIDATED')
        self.assertIs(self.gate.lifecycle,sentinel)
        self.assertIs(self.gate.request,sentinel)

    def test_lease_invalidated_externally(self):
        self.run_dispatch()
        self.d.leases.invalidate('SELECTION_CHANGED')
        self.assertEqual(self.check().reason,'PREVIEW_LEASE_INVALIDATED')

    def test_context_observer_required(self):
        del self.session.m4a_write
        self.reject('HOST_CONTEXT_UNAVAILABLE')

    def test_readonly_operation_busy(self):
        self.session.tools.pending={}
        self.reject('EXECUTION_BUSY')

    def test_clock_regression_fails_closed(self):
        self.run_dispatch()
        self.now=0
        out=self.check()
        self.assertFalse(out.accepted)
        self.assertEqual(out.reason,'INTERNAL_DISPATCH_ERROR')
        self.assertEqual(out.request.state,'COMPLETED')
        self.assertIsNone(self.d.admission.active)

    def test_target_changed_same_element_id(self):
        self.run_dispatch()
        self.f.pipe.UniqueId='other'
        self.assertEqual(self.check().reason,'PREVIEW_LEASE_INVALIDATED')

    def test_safety_lock_appearing_during_preview_is_retained(self):
        self.run_dispatch()
        self.d.admission.safety_locked=True
        self.assertEqual(self.check().reason,'UNRESOLVED_MUTATION_SAFETY')
        self.assertTrue(self.d.admission.safety_locked)

    def test_preview_request_id_mismatch(self):
        original=dispatch._preview
        def wrong(*args):
            result=original(*args)
            result['request_id']='other'
            return result
        with patch.object(dispatch,'_preview',side_effect=wrong):
            self.reject('CORRELATION_MISMATCH')
        self.assertIsNone(self.d.admission.active)

    def test_preview_target_mismatch(self):
        original=dispatch._preview
        def wrong(*args):
            result=original(*args)
            result['target_element_id']=999
            return result
        with patch.object(dispatch,'_preview',side_effect=wrong):
            self.reject('CORRELATION_MISMATCH')

    def test_preview_value_mismatch(self):
        original=dispatch._preview
        def wrong(*args):
            result=original(*args)
            result['proposed_value']='Other'
            return result
        with patch.object(dispatch,'_preview',side_effect=wrong):
            self.reject('CORRELATION_MISMATCH')


if __name__=='__main__':
    unittest.main()
