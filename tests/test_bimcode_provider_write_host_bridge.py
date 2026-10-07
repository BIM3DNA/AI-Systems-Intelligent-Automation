"""DISPATCH-002 offline native-consent/event/executor integration, no Revit."""
import ast
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock, patch
import test_bimcode_write_execution as execution_tests
from bimcode_ai_pane import provider_write as machine
from bimcode_ai_pane import provider_write_confirmation as confirmation
from bimcode_ai_pane.provider_write_dispatch import Dispatcher
from bimcode_ai_pane.provider_write_host_bridge import Bridge
from bimcode_ai_pane.session_write_gate import SessionWriteGate, read_document
from bimcode_ai_pane.write_access import admission_for
from bimcode_ai_pane.write_clock import Clock


class HostBridge(unittest.TestCase):
    def setUp(self):
        execution_tests.Execution.setUp(self)
        f = self.f
        f.doc.PathName = ''
        f.doc.IsLinked = False
        self.session = N(document_identity=(123,'Fixture',''), context_generation=0,
            selection_generation=0, m4a_write=N(epoch=0), tools=N(pending=None), ai=N(turn=None))
        self.gate = self.session.write_gate = SessionWriteGate(admission_for(self.session))
        document, facts = read_document(f.app,f.db,f.guid)
        self.gate.observe(document,facts)
        self.gate.permission.enable_from_human(document,facts,True)
        self.now = 10.0
        self.clock = Clock(lambda:self.now,lambda:'2026-10-07T12:00:00Z')
        self.identity = machine.correlation('logical','host',str(id(self.session)),document,'response','call','Value_02')
        self.d = Dispatcher(self.session,self.identity,self.clock,True)
        out = self.d._dispatch(f.app,dict(name=self.identity.tool_name,call_id='call',arguments={'value':'Value_02'}),
                               'response',f.db,f.guid)
        self.assertTrue(out.accepted)
        self.bridge = Bridge(self.session)
        self.bridge._api = lambda:(f.db,f.guid)
        self.bridge.event = N(Raise=Mock(return_value='Accepted'))
        self.ui = N(ExternalEventRequest=N(Accepted='Accepted'))
        self.modules = patch.dict(sys.modules,{'Autodesk':N(),'Autodesk.Revit':N(UI=self.ui)})
        self.modules.start()
        self.dialog = patch.object(confirmation,'show',return_value=True)
        self.show = self.dialog.start()
        self.addCleanup(self.modules.stop)
        self.addCleanup(self.dialog.stop)

    def confirm(self):
        return self.bridge.request_confirmation(self.f.app,self.d,self.identity)

    def run_host(self):
        return self.bridge.execute(self.f.app)

    def host(self):
        return json.loads(self.d.request.host_result.json)

    def no_mutation(self):
        self.f.db.Transaction.assert_not_called()
        self.f.parameter.Set.assert_not_called()

    def test_cancel(self):
        self.show.return_value=False
        self.confirm()
        self.assertEqual(self.d.request.state,'CANCELLED')
        self.assertEqual(self.host()['reason_code'],'USER_CANCELLED')
        self.assertIsNone(self.d.leases.queue.binding)
        self.bridge.event.Raise.assert_not_called()
        self.assertIsNone(self.d.admission.active)
        self.no_mutation()

    def test_confirm_then_later_handler(self):
        self.confirm()
        self.assertEqual(self.d.request.state,'WRITE_REQUEST_QUEUED')
        self.assertTrue(self.d.leases.preview.consumed)
        self.assertEqual(self.d.leases.queue.expires_at-self.d.leases.queue.created_at,30)
        self.assertIsNotNone(self.bridge.pending)
        self.no_mutation()
        self.run_host()
        self.assertEqual(self.d.request.state,'HOST_RESULT_READY')
        result=self.host()
        self.assertEqual(result['reason_code'],'COMPLETE')
        self.assertEqual(result['before_value'],None)
        self.assertEqual(result['proposed_value'],'Value_02')
        self.assertEqual(result['final_value'],'Value_02')
        self.assertTrue(result['verification_passed'])
        self.assertTrue(result['transaction_committed'])
        self.f.db.Transaction.assert_called_once()
        self.f.parameter.Set.assert_called_once_with('Value_02')
        self.tx.Commit.assert_called_once()
        self.assertEqual(self.d.sink.receipt.receipt,self.d.request.host_result)
        self.assertEqual(self.d.request.provider_status.status,'NOT_STARTED')
        self.assertIsNone(self.d.admission.active)

    def test_preview_expired_before_dialog(self):
        self.now=130
        self.confirm()
        self.assertEqual(self.host()['reason_code'],'PREVIEW_LEASE_EXPIRED')
        self.show.assert_not_called()
        self.bridge.event.Raise.assert_not_called()
        self.no_mutation()

    def test_preview_expired_in_dialog(self):
        def answer(*args):
            self.now=130
            return True
        self.show.side_effect=answer
        self.confirm()
        self.assertEqual(self.host()['reason_code'],'PREVIEW_LEASE_EXPIRED')
        self.assertIsNone(self.d.leases.queue.binding)
        self.no_mutation()

    def test_preview_invalidated(self):
        self.d.leases.invalidate('ABANDONED')
        self.confirm()
        self.assertEqual(self.host()['reason_code'],'PREVIEW_LEASE_INVALIDATED')
        self.no_mutation()

    def test_double_confirm(self):
        self.confirm()
        self.assertEqual(self.confirm(),'EXECUTION_BUSY')
        self.show.assert_called_once()
        self.bridge.event.Raise.assert_called_once()

    def test_mismatched_identity(self):
        self.assertEqual(self.bridge.request_confirmation(self.f.app,self.d,self.identity._replace(call_id='other')),
                         'CORRELATION_MISMATCH')
        self.show.assert_not_called()
        self.no_mutation()

    def test_no_consent_argument(self):
        with self.assertRaises(TypeError):
            self.bridge.request_confirmation(self.f.app,self.d,self.identity,True)
        self.no_mutation()

    def test_raise_nonaccepted(self):
        self.bridge.event.Raise.return_value='Pending'
        self.confirm()
        self.assertEqual(self.host()['reason_code'],'EXTERNAL_EVENT_NOT_ACCEPTED')
        self.assertIsNone(self.bridge.pending)
        self.run_host()
        self.no_mutation()

    def test_raise_denied(self):
        self.bridge.event.Raise.return_value='Denied'
        self.confirm()
        self.assertEqual(self.host()['reason_code'],'EXTERNAL_EVENT_NOT_ACCEPTED')
        self.no_mutation()

    def test_raise_exception(self):
        self.bridge.event.Raise.side_effect=RuntimeError('private')
        self.confirm()
        self.assertEqual(self.host()['reason_code'],'EXTERNAL_EVENT_NOT_ACCEPTED')
        self.assertNotIn('private',str(self.d.request))
        self.no_mutation()

    def test_queue_expired_exact_boundary(self):
        self.confirm()
        self.now=40
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'EXECUTION_QUEUE_LEASE_EXPIRED')
        self.no_mutation()

    def test_queue_invalidated(self):
        self.confirm()
        self.d.leases.invalidate('ABANDONED')
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'EXECUTION_QUEUE_LEASE_INVALIDATED')
        self.no_mutation()

    def test_stale_epoch(self):
        self.confirm()
        self.session.m4a_write.epoch+=1
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'STALE_CONTEXT')
        self.no_mutation()

    def test_context_generation(self):
        self.confirm()
        self.session.context_generation+=1
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'STALE_CONTEXT')
        self.no_mutation()

    def test_competing_owner(self):
        self.confirm()
        self.d.admission.active=self.d.owner._replace(token='other')
        self.run_host()
        self.no_mutation()

    def test_target_missing(self):
        self.confirm()
        original=self.f.doc.GetElement
        self.f.doc.GetElement=lambda eid:None if eid.Value==1 else original(eid)
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'TARGET_MISSING')
        self.no_mutation()

    def test_parameter_readonly(self):
        self.confirm()
        self.f.parameter.IsReadOnly=True
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'TARGET_NOT_WRITABLE')
        self.no_mutation()

    def test_before_value_changed(self):
        self.confirm()
        self.value='Changed'
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'PRECONDITION_CHANGED')
        self.no_mutation()

    def test_lifecycle_before_execution(self):
        self.confirm()
        self.gate.cleanup('DOCUMENT_CLOSE')
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'EXECUTION_QUEUE_LEASE_INVALIDATED')
        self.no_mutation()

    def test_completion_survives_cleanup(self):
        self.confirm();self.run_host()
        receipt=self.d.sink.receipt
        self.gate.cleanup('PANE_DISPOSAL')
        self.assertEqual(self.d.sink.receipt,receipt)
        self.assertEqual(self.d.request.host_result,receipt.receipt)

    def test_replay(self):
        self.confirm();self.run_host();self.run_host()
        self.f.db.Transaction.assert_called_once()
        self.f.parameter.Set.assert_called_once()

    def test_set_failure(self):
        self.confirm()
        self.f.parameter.Set.side_effect=RuntimeError('set')
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'PARAMETER_SET_FAILED')
        self.tx.RollBack.assert_called_once()

    def test_start_failure(self):
        self.confirm()
        self.tx.Start.side_effect=RuntimeError('start')
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'TRANSACTION_START_FAILED')
        self.f.parameter.Set.assert_not_called()

    def test_commit_failure(self):
        self.confirm()
        self.tx.Commit.side_effect=RuntimeError('commit')
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'TRANSACTION_COMMIT_FAILED')

    def test_pending_safety_retained(self):
        self.confirm()
        def commit():
            self.status='Pending'
            return 'Pending'
        self.tx.Commit.side_effect=commit
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'TRANSACTION_PENDING')
        self.assertTrue(self.d.admission.safety_locked)
        self.assertIsNotNone(self.bridge.executor.retained)
        self.run_host()
        self.f.parameter.Set.assert_called_once()

    def test_rollback_unconfirmed(self):
        self.confirm()
        self.f.parameter.Set.side_effect=RuntimeError('set')
        self.tx.RollBack.side_effect=RuntimeError('rollback')
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'ROLLBACK_UNCONFIRMED')
        self.assertTrue(self.d.admission.safety_locked)

    def test_verification_failure(self):
        self.confirm()
        self.f.parameter.Set.side_effect=lambda v:True
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'VERIFICATION_FAILED')
        self.assertTrue(self.host()['model_modified'])

    def test_late_confirm_does_not_reuse_m4a_timer(self):
        self.now=100
        self.confirm()
        self.now=125
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'COMPLETE')

    def test_native_dialog_cancel_default(self):
        self.dialog.stop()
        dialog=Mock()
        dialog.Show.return_value='Cancel'
        self.ui.TaskDialog=Mock(return_value=dialog)
        self.ui.TaskDialogCommandLinkId=N(CommandLink1='Confirm')
        self.ui.TaskDialogCommonButtons=N(Cancel='Cancel')
        self.ui.TaskDialogResult=N(Cancel='Cancel',CommandLink1='Confirm')
        self.assertFalse(confirmation.show(json.loads(self.d.preview_json),self.identity))
        self.assertEqual(dialog.DefaultButton,'Cancel')
        self.assertTrue(dialog.AllowCancellation)
        for value in ('Pipe 1',self.identity.logical_request_id,self.identity.host_request_id,'Value_02'):
            self.assertIn(value,dialog.MainContent)

    def test_clock_failure_before_execution(self):
        self.confirm()
        self.now=0
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'CLOCK_STATE_INVALID')
        self.no_mutation()

    def test_consumed_preview_cannot_confirm(self):
        self.d.leases.confirm(self.d.context_binding,True)
        self.confirm()
        self.assertEqual(self.host()['reason_code'],'LEASE_ALREADY_CONSUMED')
        self.show.assert_not_called()
        self.no_mutation()

    def test_target_changed(self):
        self.confirm()
        self.f.pipe.UniqueId='other'
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'TARGET_CHANGED')
        self.no_mutation()

    def test_parameter_missing(self):
        self.confirm()
        self.f.pipe.get_Parameter=lambda guid:None
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'PARAMETER_MISSING')
        self.no_mutation()

    def test_storage_changed(self):
        self.confirm()
        self.f.parameter.StorageType='Integer'
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'STORAGE_TYPE_UNSUPPORTED')
        self.no_mutation()

    def test_safety_lock_before_handler(self):
        self.confirm()
        self.d.admission.safety_locked=True
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'UNRESOLVED_MUTATION_SAFETY')
        self.assertTrue(self.d.admission.safety_locked)
        self.no_mutation()

    def test_document_switch_during_dialog(self):
        def answer(*args):
            self.gate.cleanup('DOCUMENT_SWITCH')
            return True
        self.show.side_effect=answer
        self.confirm()
        self.bridge.event.Raise.assert_not_called()
        self.no_mutation()

    def test_session_lifecycle_triggers(self):
        for trigger in ('DOCUMENT_SWITCH','DOCUMENT_CLOSE','PANE_DISPOSAL','SHUTDOWN','ABANDONED'):
            with self.subTest(trigger=trigger):
                # New test instance prevents replay/permission state reuse.
                case=HostBridge('test_lifecycle_before_execution')
                case.setUp()
                try:
                    case.confirm()
                    case.gate.cleanup(trigger)
                    case.run_host()
                    case.no_mutation()
                    self.assertIsNotNone(case.d.request.host_result)
                finally:
                    case.doCleanups()

    def test_competing_admissions_blocked(self):
        for owner in ('HUMAN_DEV_WRITE','CONTROLLED_WRITE_PROVIDER_TOOL','PARAMETER_PROVISIONING'):
            try:
                acquired=self.d.admission.acquire(owner,'other','other',self.identity.document_id,
                                                   self.identity.session_id,10)
            except ValueError:
                acquired=None
            self.assertIsNone(acquired)

    def test_unknown_transaction_status(self):
        self.confirm()
        def commit():
            self.status='Unknown'
            return self.status
        self.tx.Commit.side_effect=commit
        self.run_host()
        self.assertEqual(self.host()['reason_code'],'TRANSACTION_STATUS_UNKNOWN')
        self.assertTrue(self.d.admission.safety_locked)

    def test_single_session_event_lifetime(self):
        from bimcode_ai_pane.provider_write_host_bridge import get_bridge
        coordinator=N(get_coordinator=Mock())
        self.ui.IExternalEventHandler=object
        self.ui.ExternalEvent=N(Create=Mock(return_value=self.bridge.event))
        with patch.dict(sys.modules,{'bimcode_ai_pane.write_coordinator':coordinator}):
            first=get_bridge(self.session)
            self.assertIs(first,get_bridge(self.session))
            self.ui.ExternalEvent.Create.assert_called_once_with(first.handler)
            first.execute=Mock()
            first.handler.Execute(self.f.app)
            first.execute.assert_called_once_with(self.f.app)

    def test_new_modules_have_no_mutation_network_continuation(self):
        root=Path(__file__).resolve().parents[1]/'AI.extension/lib/bimcode_ai_pane'
        for name in ('provider_write_confirmation.py','provider_write_host_bridge.py'):
            tree=ast.parse((root/name).read_text())
            calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
            for forbidden in ('Set','Transaction','send_write_explanation','deliver'):
                self.assertNotIn(forbidden,calls)


if __name__=='__main__':
    unittest.main()
