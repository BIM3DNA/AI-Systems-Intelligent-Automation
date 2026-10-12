"""Internal recorded-shape provenance and actual host/coordinator integration."""
import copy
import json
import unittest
from types import SimpleNamespace as N
from unittest.mock import patch
import test_bimcode_provider_write_host_bridge as host_tests
from bimcode_ai_pane import provider_write_handoff as h
from bimcode_ai_pane.provider_write_session import SessionWrites


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.f = f = host_tests.HostBridge()
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.s = s = f.session
        s.controlled_writes = SessionWrites(s)
        s.controlled_writes.dispatcher = f.d
        self.h = s.controlled_writes.handoff
        self.active = dict(request_id='transport', operation='agent_turn')
        s.panel = N(_provider_state=N(active=self.active))
        s.ai.turn = dict(request_id='transport', key=s.document_identity,
                         generation=0, selection=0, used=False)
        self.response = dict(protocol_version=1, request_id='transport', ok=True, provider='openai',
            model='fixture-model', text=None, error=None, state='TOOL_REQUEST',
            tool_call=dict(name='set_selected_pipe_test_text', call_id='call', arguments=dict(value='Value_02')),
            provider_state=dict(response_id='response', model='fixture-model'))
        self.ticket = self.h.open_transport(self.active, 'fixture-model')
        self.worker = patch.object(h.continuation.Coordinator, 'run_worker', side_effect=AssertionError('NETWORK'))
        self.worker.start(); self.addCleanup(self.worker.stop)

    def bind(self, response=None):
        with patch.object(h, 'uuid4', side_effect=[N(hex='logical'), N(hex='host')]):
            return self.h.bind_response(self.ticket, response or self.response)

    def finish(self, cancel=False):
        self.bind()
        self.f.show.return_value = not cancel
        self.f.confirm()
        if not cancel: self.f.run_host()
        return self.h.inspect()

    def test_success(self):
        state = self.finish()
        self.assertEqual(state['state'], 'PROVIDER_CONTINUATION_PENDING')
        self.assertIsNone(self.f.d.admission.active)
        self.assertTrue(self.f.d.sink.closed)
        self.assertTrue(self.f.d.sink.delivered)
        self.assertTrue(self.f.d.sink.continuation_claimed)
        self.assertEqual(self.f.d.request.host_result, self.h.pending[2].host_result)
        self.assertTrue(self.s.write_gate.permission.view_model()['enabled'])

    def test_cancel(self):
        self.finish(True)
        self.assertEqual(self.f.host()['reason_code'], 'USER_CANCELLED')
        self.f.no_mutation()
        self.h.invalidate('DOCUMENT_CLOSE')
        self.assertEqual(self.f.d.request.state, 'CANCELLED')

    def test_owner_active_at_begin(self):
        original = h.continuation.Coordinator.begin
        observed=[]
        def begin(coordinator, request, sink, admission, model, stamp):
            observed.append((sink.delivered, sink.closed, admission.active == sink.owner, request.state))
            return original(coordinator, request, sink, admission, model, stamp)
        with patch.object(h.continuation.Coordinator, 'begin', begin): self.finish()
        self.assertEqual(observed, [(True, False, True, 'HOST_RESULT_READY')])

    def test_pending_exclusive_inspection(self):
        self.finish()
        before=self.h.pending[2]
        for _ in range(3):
            self.s.controlled_writes.inspect()
            self.assertEqual(json.loads(self.s.controlled_writes.begin('Other'))['reason'], 'CONTINUATION_PENDING')
        self.assertIs(self.h.pending[2], before)
        self.assertFalse(self.h.admit(self.f.d))

    def test_shared_admission_blocked(self):
        self.finish()
        self.s.ai.turn=None
        admission=self.f.d.admission
        self.assertIsNone(admission.acquire('HUMAN_DEV_WRITE','other','other',self.f.identity.document_id,
                                           str(id(self.s)),10))

    def test_hold_expiry(self):
        self.finish()
        receipt=self.f.d.request.host_result
        self.f.now += 120
        state=self.h.inspect()
        self.assertFalse(state['pending'])
        self.assertEqual(state['last']['reason'], 'CONTINUATION_HOLD_EXPIRED')
        self.assertEqual(self.f.d.request.host_result, receipt)
        self.assertEqual(self.f.d.request.state, 'COMPLETED')

    def test_lifecycle(self):
        self.finish()
        receipt=self.f.d.request.host_result
        for reason in ('DOCUMENT_SWITCH','DOCUMENT_CLOSE','PANE_DISPOSAL','SHUTDOWN','ABANDONED'):
            self.s.write_gate.cleanup(reason)
        self.assertIsNone(self.h.pending)
        self.assertEqual(self.f.d.request.host_result,receipt)
        self.assertFalse(self.s.write_gate.permission.view_model()['enabled'])

    def test_arbitrary_dictionary(self):
        with self.assertRaises(ValueError): self.h.bind_response(self.ticket._asdict(),self.response)

    def test_missing_outstanding(self):
        self.s.panel._provider_state.active=None
        with self.assertRaises(ValueError): self.bind()

    def test_stale_turn(self):
        self.s.ai.turn=dict(self.s.ai.turn)
        with self.assertRaises(ValueError): self.bind()

    def test_replaced_transport(self):
        self.s.panel._provider_state.active=dict(self.active)
        with self.assertRaises(ValueError): self.bind()

    def test_stale_document(self):
        self.s.document_identity=('other',)
        with self.assertRaises(ValueError): self.bind()

    def test_stale_generation(self):
        self.s.context_generation += 1
        with self.assertRaises(ValueError): self.bind()

    def test_response_model_mismatch(self):
        self.response['provider_state']['model']='other'
        with self.assertRaises(ValueError): self.bind()

    def test_transport_id_mismatch(self):
        self.response['request_id']='other'
        with self.assertRaises(ValueError): self.bind()

    def test_unverified_success_rejected(self):
        from bimcode_ai_pane.write_projection import freeze_result
        self.finish()
        result=self.f.host();result['verification_passed']=False
        with self.assertRaises(ValueError): freeze_result(result)

    def test_incomplete_receipt_rejected(self):
        from bimcode_ai_pane.write_projection import freeze_result
        with self.assertRaises(ValueError):freeze_result(dict(classification='MEP_PARAMETER_WRITE_OK'))

    def test_each_lifecycle_invalidation(self):
        for reason in ('DOCUMENT_SWITCH','DOCUMENT_CLOSE','PANE_DISPOSAL','SHUTDOWN','ABANDONED'):
            case=HandoffTests();case.setUp()
            try:
                case.finish();receipt=case.f.d.request.host_result
                case.s.write_gate.cleanup(reason)
                self.assertIsNone(case.h.pending)
                self.assertEqual(case.f.d.request.host_result,receipt)
                self.assertEqual(case.f.d.request.provider_status.status,'UNAVAILABLE')
            finally:case.doCleanups()

    def test_model_mismatch(self):
        self.response['model']='other'
        with self.assertRaises(ValueError): self.bind()

    def test_wrong_tool(self):
        self.response['tool_call']['name']='other'
        with self.assertRaises(ValueError): self.bind()

    def test_injected_target(self):
        self.response['tool_call']['arguments']['ElementId']=1
        with self.assertRaises(ValueError): self.bind()

    def test_synthetic_response(self):
        self.response['provider_state']['response_id']='host-test-response-1'
        with self.assertRaises(ValueError): self.bind()

    def test_synthetic_call(self):
        self.response['tool_call']['call_id']='host-test-call-1'
        with self.assertRaises(ValueError): self.bind()

    def test_duplicate_response(self):
        self.h.seen.add(('response','different_call'))
        with self.assertRaises(ValueError): self.bind()

    def test_duplicate_call_after_expiry(self):
        self.finish();self.f.now += 120;self.h.check()
        self.s.ai.turn=dict(request_id='transport2',key=self.s.document_identity,generation=0,selection=0,used=False)
        active=dict(request_id='transport2',operation='agent_turn')
        self.s.panel._provider_state.active=active
        ticket=self.h.open_transport(active,'fixture-model')
        response=copy.deepcopy(self.response)
        response['request_id']='transport2'
        response['provider_state']['response_id']='response2'
        with self.assertRaises(ValueError): self.h.bind_response(ticket,response)

    def test_capacity(self):
        self.h.seen=set((str(i),str(i)) for i in range(h.LEDGER_LIMIT))
        with self.assertRaises(ValueError): self.bind()

    def test_atomic_duplicate_call(self):
        self.h.seen.add(('old_response','call'))
        before=set(self.h.seen)
        with self.assertRaises(ValueError):self.bind()
        self.assertEqual(self.h.seen,before)

    def test_atomic_duplicate_response(self):
        self.h.seen.add(('response','old_call'))
        before=set(self.h.seen)
        with self.assertRaises(ValueError):self.bind()
        self.assertEqual(self.h.seen,before)

    def test_duplicate_pair(self):
        self.h.seen.add(('response','call'))
        with self.assertRaises(ValueError):self.bind()
        self.assertEqual(len(self.h.seen),1)

    def test_exact_capacity_and_no_eviction(self):
        self.h.seen=set(('r'+str(i),'c'+str(i)) for i in range(999))
        self.bind()
        self.assertEqual(len(self.h.seen),1000)
        before=set(self.h.seen)
        self.h.binding=None;self.s.ai.turn['used']=False
        self.ticket=self.h.open_transport(self.active,'fixture-model')
        self.response['provider_state']['response_id']='new_response'
        self.response['tool_call']['call_id']='new_call'
        with self.assertRaises(ValueError):self.bind()
        self.assertEqual(self.h.seen,before)
        self.ticket=self.h.open_transport(self.active,'fixture-model')
        self.response['provider_state']['response_id']='response'
        with self.assertRaises(ValueError):self.bind()
        self.assertEqual(self.h.seen,before)

    def test_invalid_then_valid_no_reservation(self):
        invalid=copy.deepcopy(self.response);invalid['model']='wrong'
        with self.assertRaises(ValueError):self.bind(invalid)
        self.assertEqual(self.h.seen,set())
        self.ticket=self.h.open_transport(self.active,'fixture-model')
        self.bind()
        self.assertEqual(self.h.seen,{('response','call')})

    def test_reentrant_binding(self):
        def generate():
            with self.assertRaisesRegex(ValueError,'PROVIDER_BINDING_BUSY'):
                self.h.bind_response(self.ticket,self.response)
            return N(hex='generated')
        with patch.object(h,'uuid4',side_effect=generate):self.h.bind_response(self.ticket,self.response)
        self.assertEqual(self.h.seen,{('response','call')})

    def test_session_lifetime_isolation(self):
        self.bind()
        other=h.Handoff(self.s)
        self.assertEqual(other.seen,set())
        for reason in ('DOCUMENT_CLOSE','PANE_DISPOSAL','SHUTDOWN'):
            self.h.invalidate(reason)
            self.assertEqual(self.h.seen,{('response','call')})

    def test_replay_after_release_and_lifecycle(self):
        for reason in ('CONTINUATION_HOLD_EXPIRED','DOCUMENT_CLOSE','PANE_DISPOSAL'):
            case=HandoffTests();case.setUp()
            try:
                case.finish();self.assertIsNone(case.f.d.admission.active)
                case.h.invalidate(reason)
                case.s.ai.turn=dict(request_id='later',key=case.s.document_identity,generation=0,selection=0,used=False)
                active=dict(request_id='later',operation='agent_turn');case.s.panel._provider_state.active=active
                ticket=case.h.open_transport(active,'fixture-model')
                response=copy.deepcopy(case.response);response['request_id']='later'
                response['provider_state']['response_id']='later_response'
                with self.assertRaises(ValueError):case.h.bind_response(ticket,response)
                self.assertEqual(case.h.seen,{('response','call')})
            finally:case.doCleanups()

    def test_concurrent_duplicate_binding(self):
        import threading
        barrier=threading.Barrier(2);results=[]
        def attempt():
            barrier.wait()
            try:self.h.bind_response(self.ticket,copy.deepcopy(self.response));results.append('accepted')
            except ValueError:results.append('rejected')
        threads=[threading.Thread(target=attempt) for _ in range(2)]
        for thread in threads:thread.start()
        for thread in threads:thread.join(5)
        self.assertEqual(sorted(results),['accepted','rejected'])
        self.assertEqual(self.h.seen,{('response','call')})

    def test_stale_document_well_formed_receipt(self):
        self.bind();self.f.confirm()
        self.s.document_identity=('changed',)
        self.f.run_host()
        self.assertIsNone(self.h.pending)
        self.assertIsNotNone(self.f.d.request.host_result)

    def test_stale_session_well_formed_receipt(self):
        self.bind()
        self.h.binding=self.h.binding._replace(identity=self.h.binding.identity._replace(session_id='stale'))
        self.f.confirm();self.f.run_host()
        self.assertIsNone(self.h.pending)
        self.assertEqual(self.f.host()['classification'],'MEP_PARAMETER_WRITE_OK')

    def test_missing_receipt(self):
        self.bind()
        self.assertFalse(self.h.admit(self.f.d))
        self.assertEqual(self.h.failure,'CONTINUATION_ADMISSION_FAILED')

    def test_full_correlation(self):
        self.bind()
        self.h.binding=self.h.binding._replace(identity=self.h.binding.identity._replace(call_id='other'))
        self.f.confirm();self.f.run_host()
        self.assertIsNone(self.h.pending)
        self.assertEqual(self.f.host()['classification'],'MEP_PARAMETER_WRITE_OK')
        self.assertIsNone(self.f.d.admission.active)

    def test_preview_expiry(self):
        self.bind();self.f.now += 120
        self.f.confirm()
        self.assertEqual(self.f.host()['reason_code'],'PREVIEW_LEASE_EXPIRED')
        self.assertIsNotNone(self.h.pending)
        self.f.no_mutation()

    def test_queue_expiry(self):
        self.bind();self.f.confirm();self.f.now += 30;self.f.run_host()
        self.assertEqual(self.f.host()['reason_code'],'EXECUTION_QUEUE_LEASE_EXPIRED')
        self.assertIsNotNone(self.h.pending)
        self.f.no_mutation()

    def test_event_rejection(self):
        self.bind();self.f.bridge.event.Raise.return_value='Denied';self.f.confirm()
        self.assertEqual(self.f.host()['reason_code'],'EXTERNAL_EVENT_NOT_ACCEPTED')
        self.assertIsNotNone(self.h.pending)

    def test_immutable_inspection(self):
        self.finish()
        state=self.h.inspect();state['correlation']['call_id']='forged'
        self.assertEqual(self.h.inspect()['correlation']['call_id'],'call')

    def test_late_callback(self):
        self.finish();self.h.invalidate('PANE_DISPOSAL')
        self.assertIsNone(self.f.run_host())
        self.assertIsNone(self.h.pending)

    def test_no_transport(self):
        self.finish()
        self.assertFalse(self.h.pending[1]._worker_started)

    def test_rollback(self):
        self.bind();self.f.f.parameter.Set.side_effect=RuntimeError('fixture')
        self.f.confirm();self.f.run_host()
        self.assertIsNotNone(self.h.pending)
        self.assertEqual(self.f.host()['transaction_status'],'RolledBack')
        self.assertEqual(self.f.host()['classification'],'MEP_PARAMETER_WRITE_FAILED')

    def test_indeterminate(self):
        self.bind()
        def commit():
            self.f.status='Pending'
            return 'Pending'
        self.f.tx.Commit.side_effect=commit
        self.f.confirm();self.f.run_host()
        self.assertIsNotNone(self.h.pending)
        self.assertTrue(self.f.d.admission.safety_locked)
        receipt=self.f.d.request.host_result
        self.h.invalidate('DOCUMENT_CLOSE')
        self.assertTrue(self.f.d.admission.safety_locked)
        self.assertEqual(self.f.d.request.host_result,receipt)

    def test_each_correlation_mismatch(self):
        # Fresh authoritative fixture for each independent mismatch.
        for field in ('session_id','document_id','logical_request_id','host_request_id',
                      'previous_response_id','call_id','tool_name','value'):
            with self.subTest(field=field):
                case=HandoffTests();case.setUp()
                try:
                    case.bind()
                    b=case.h.binding
                    case.h.binding=b._replace(identity=b.identity._replace(**{field:'wrong'}))
                    case.f.confirm();case.f.run_host()
                    self.assertIsNone(case.h.pending)
                    self.assertEqual(case.h.failure,'CONTINUATION_ADMISSION_FAILED')
                finally:case.doCleanups()

    def test_preview_classifications(self):
        from bimcode_ai_pane import write_projection as p
        for kind in ('OK','NOT_READY','FAILED'):
            case=HandoffTests();case.setUp()
            try:
                case.bind()
                data=json.loads(case.f.d.preview_json)
                data['classification']='MEP_PARAMETER_WRITE_PREVIEW_'+kind
                receipt=p.from_preview(data)
                case.f.d.sink.store(p.project_receipt(receipt))
                case.f.d.request=case.f.d.request._replace(state='HOST_RESULT_READY',host_result=receipt)
                self.assertFalse(case.h.admit(case.f.d))
                self.assertIsNone(case.h.pending)
            finally:case.doCleanups()
