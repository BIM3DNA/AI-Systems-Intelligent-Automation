"""003B-2A ownership only. Fake context; no preview or execution under test."""
import unittest
from unittest.mock import patch
import test_bimcode_provider_write_adapter as fixtures
from bimcode_ai_pane import provider_write_transfer as transfer
from bimcode_ai_pane.provider_write_dispatch import Dispatcher


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.AdapterTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.s = self.f.s
        self.w = self.s.controlled_writes
        self.t = self.w.transfer
        self.m = self.s.write_gate.admission
        # Remove fixture's prebuilt host-only preview ownership; no API is run.
        self.m._active = None  # Fixture reset; public owner is read-only.
        self.s.write_gate.lifecycle = None
        self.s.write_gate.request = None
        self.w.dispatcher = None
        self.f.bind()

    def reserve(self):
        self.assertEqual(self.t.reserve()['state'], 'PROVIDER_TURN_RESERVED')

    def advance(self):
        self.reserve()
        self.assertEqual(self.t.transfer()['state'], 'CONTROLLED_WRITE_OWNER_TRANSFERRED')

    def reject(self, change):
        self.reserve()
        owner = self.m.active
        evidence = self.w.adapter.accepted
        change()
        with self.assertRaises(ValueError): self.t.transfer()
        self.assertIs(self.w.adapter.accepted, evidence)
        self.assertIsNone(self.t.transferred)
        return owner

    def test_reservation(self):
        self.reserve()
        self.assertIs(self.m.active, self.t.reservation.owner)
        self.assertEqual(self.m.active.owner_type, 'PROVIDER_TURN')
        self.assertIs(self.t.reservation.evidence, self.w.adapter.accepted)

    def test_valid_transfer(self):
        self.advance()
        self.assertIs(self.m.active, self.t.transferred)
        self.assertEqual(self.m.active.owner_type, 'CONTROLLED_WRITE_PROVIDER_TOOL')
        self.assertIs(self.s.ai.turn, self.t.reservation.evidence[0].ticket.turn)
        self.assertTrue(self.s.ai.turn['used'])

    def test_exact_owner(self):
        self.reserve()
        self.m._active = self.m.active._replace()  # Deliberate identity fault injection.
        with self.assertRaises(ValueError): self.t.transfer()

    def test_no_gap_or_reentry(self):
        self.reserve()
        owner = self.m.active
        original = transfer.uuid4
        def creating():
            self.assertIs(self.m.active, owner)
            self.assertIsNone(self.m.acquire('HUMAN_DEV_WRITE','x','x','d','s',1))
            self.assertFalse(self.m.release(owner,'REENTRANT'))
            with self.assertRaises(ValueError): self.t.transfer()
            return original()
        with patch.object(transfer, 'uuid4', side_effect=creating): self.t.transfer()
        self.assertIs(self.m.active, self.t.transferred)

    def test_reservation_one_use(self):
        self.reserve()
        with self.assertRaises(ValueError): self.t.reserve()

    def test_transfer_one_use(self):
        self.advance()
        owner = self.m.active
        with self.assertRaises(ValueError): self.t.transfer()
        self.assertIs(self.m.active, owner)

    def test_adoption(self):
        self.advance()
        self.assertEqual(self.t.adopt()['state'], 'TRANSFERRED_OWNER_ADOPTED')
        d = self.w.dispatcher
        self.assertIs(d.owner, self.m.active)
        self.assertIs(d.identity, self.w.handoff.binding.identity)
        self.assertTrue(d.used)
        self.assertIsNone(d.request)
        self.assertIsNone(d.preview_json)

    def test_adoption_one_use(self):
        self.advance(); self.t.adopt()
        d = self.w.dispatcher
        with self.assertRaises(ValueError): self.t.adopt()
        self.assertIs(self.w.dispatcher, d)

    def test_arbitrary_dispatcher(self):
        self.advance()
        d = Dispatcher(self.s, self.w.handoff.binding.identity)
        with self.assertRaises(ValueError): d.adopt_transferred()

    def test_adoption_before_transfer(self):
        self.reserve()
        with self.assertRaises(ValueError): self.t.adopt()

    def test_sealed_dispatcher(self):
        self.advance(); self.t.adopt()
        with patch('bimcode_ai_pane.provider_write_dispatch.capture_preview_context',
                   side_effect=AssertionError('preview')):
            result = self.w.dispatcher._dispatch(None, None, None, None, None)
        self.assertFalse(result.accepted)
        self.assertIsNone(self.w.dispatcher.preview_json)

    def test_competing_request(self):
        self.advance()
        self.assertIsNone(self.m.acquire('HUMAN_DEV_WRITE','x','x','d','s',1))

    def test_unrelated_owner(self):
        self.reserve()
        outsider = self.m.active._replace(token='outsider')
        self.m._active = outsider  # Deliberate competing-owner fault injection.
        with self.assertRaises(ValueError): self.t.transfer()
        self.t.invalidate('DOCUMENT_CLOSE')
        self.assertIs(self.m.active, outsider)

    def test_pending_m2(self):
        self.reject(lambda: setattr(self.s.tools, 'pending', object()))

    def test_write_busy(self):
        self.reject(lambda: setattr(self.s, 'write_busy', True))

    def test_pending_continuation(self):
        self.reject(lambda: setattr(self.w.handoff, 'pending', object()))

    def test_safety_lock(self):
        self.reject(lambda: setattr(self.m, 'safety_locked', True))
        self.t.invalidate('ABANDONED')
        self.assertTrue(self.m.safety_locked)

    def test_wrong_document(self):
        self.reject(lambda: setattr(self.s, 'document_identity', ('wrong',)))

    def test_wrong_session(self):
        self.reject(lambda: setattr(self.s, 'controlled_writes', object()))

    def test_wrong_turn_identity(self):
        self.reject(lambda: setattr(self.s.ai, 'turn', dict(self.s.ai.turn)))

    def test_wrong_turn_generation(self):
        self.reject(lambda: self.s.ai.turn.update(generation=99))

    def test_stale_selection(self):
        self.reject(lambda: setattr(self.s, 'selection_generation', 99))

    def test_stale_context(self):
        self.reject(lambda: setattr(self.s, 'context_generation', 99))

    def test_model_epoch(self):
        self.reject(lambda: setattr(self.s.m4a_write, 'epoch', 99))

    def test_permission_generation(self):
        self.reject(lambda: self.s.write_gate.permission.disable())

    def test_readiness_generation(self):
        self.reject(lambda: setattr(self.w.adapter, 'model_generation', 99))

    def test_transport_identity(self):
        self.reject(lambda: setattr(self.s.panel._provider_state, 'active', dict(self.f.active)))

    def test_binding_identity(self):
        self.reject(lambda: setattr(self.w.handoff, 'binding', self.w.handoff.binding._replace()))

    def test_invalid_eligibility(self):
        self.reject(lambda: self.s.write_gate.facts.update(read_only=True))

    def test_lifecycle(self):
        for reason in ('ABANDONED','DOCUMENT_SWITCH','DOCUMENT_CLOSE','PANE_DISPOSAL','SHUTDOWN'):
            for adopted in (False, True):
                with self.subTest(reason=reason, adopted=adopted):
                    f = TransferTests(); f.setUp()
                    try:
                        f.advance()
                        if adopted: f.t.adopt()
                        evidence = f.w.adapter.accepted
                        f.s.write_gate.cleanup(reason)
                        self.assertIsNone(f.m.active)
                        self.assertIs(f.w.adapter.accepted, evidence)
                        with self.assertRaises(ValueError): f.t.transfer()
                        with self.assertRaises(ValueError): f.t.adopt()
                    finally: f.doCleanups()

    def test_lifecycle_during_construction(self):
        self.reserve(); owner = self.m.active
        original = transfer.uuid4
        def closing():
            self.s.write_gate.cleanup('DOCUMENT_CLOSE')
            return original()
        with patch.object(transfer, 'uuid4', side_effect=closing):
            with self.assertRaises(ValueError): self.t.transfer()
        self.assertIs(self.m.active, owner)  # Fail closed while lock is held.
        self.assertIsNone(self.t.transferred)
        self.t.invalidate('DOCUMENT_CLOSE')
        self.assertIsNone(self.m.active)

    def test_construction_failure_atomic(self):
        self.reserve(); owner = self.m.active
        with patch.object(transfer, 'uuid4', side_effect=RuntimeError('fixture')):
            with self.assertRaises(RuntimeError): self.t.transfer()
        self.assertIs(self.m.active, owner)
        self.assertIsNone(self.t.transferred)

    def test_adoption_failure_retains_owner(self):
        self.advance(); owner = self.m.active
        self.s.selection_generation += 1
        with self.assertRaises(ValueError): self.t.adopt()
        self.assertIs(self.m.active, owner)
        self.assertFalse(self.t.adopted)
        self.assertIsNone(self.w.dispatcher)

    def test_reserve_failure_atomic(self):
        self.s.tools.pending = object()
        with self.assertRaises(ValueError): self.t.reserve()
        self.assertIsNone(self.m.active)
        self.assertIsNone(self.t.reservation)

    def test_no_reservation_from_dictionary(self):
        self.w.adapter.accepted = None
        with self.assertRaises(ValueError): self.t.reserve()

    def test_ordinary_busy_unchanged(self):
        self.assertTrue(self.m.busy())
        self.assertIsNone(self.m.acquire('HUMAN_DEV_WRITE','x','x','d','s',1))
        self.reserve()
        self.assertTrue(self.m.busy())
        self.assertFalse(self.m.busy(self.t.reservation))
        self.assertTrue(self.m.busy(self.t.reservation._replace()))

    def test_no_downstream(self):
        from bimcode_ai_pane.provider_write_host_bridge import Bridge
        from bimcode_ai_pane.write_continuation import Coordinator
        with patch.object(Dispatcher, 'dispatch', side_effect=AssertionError('dispatch')), \
                patch.object(Bridge, 'request_confirmation', side_effect=AssertionError('confirmation')), \
                patch.object(Coordinator, 'begin', side_effect=AssertionError('continuation')), \
                patch.object(Coordinator, 'run_worker', side_effect=AssertionError('worker')):
            self.advance(); self.t.adopt()
        self.f.f.f.no_mutation()

    def test_concurrent_transfer(self):
        import threading
        self.reserve()
        barrier = threading.Barrier(2)
        results = []
        def attempt():
            barrier.wait()
            try: self.t.transfer(); results.append('accepted')
            except ValueError: results.append('rejected')
        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join(5)
        self.assertEqual(sorted(results), ['accepted','rejected'])

    def test_stale_turn_cannot_revive(self):
        self.reserve()
        turn = self.s.ai.turn
        self.s.ai.turn = None
        with self.assertRaises(ValueError): self.t.transfer()
        self.s.ai.turn = turn
        with self.assertRaises(ValueError): self.t.transfer()
        self.assertTrue(self.t.invalidated)

    def test_new_binding_after_cleanup(self):
        self.advance()
        gate = self.s.write_gate
        document, facts = gate.document, dict(gate.facts)
        gate.cleanup('ABANDONED')
        gate.permission.enable_from_human(document, facts, True)
        self.s.ai.turn = dict(request_id='next', key=self.s.document_identity,
                             generation=0, selection=0, used=False)
        self.f.active = dict(request_id='next', operation='agent_turn')
        self.s.panel._provider_state.active = self.f.active
        self.f.response['request_id'] = 'next'
        self.f.response['provider_state']['response_id'] = 'next_response'
        self.f.response['tool_call']['call_id'] = 'next_call'
        self.f.bind()
        self.advance()
        self.assertFalse(self.t.invalidated)

    def test_same_binding_cannot_rereserve_after_cleanup(self):
        self.advance()
        self.t.invalidate('ABANDONED')
        with self.assertRaises(ValueError): self.t.reserve()

    def test_duplicate_callback_cannot_replace_reservation(self):
        self.reserve()
        reservation = self.t.reservation
        launch = self.w.adapter.accepted[0]
        with self.assertRaises(ValueError): self.w.adapter.complete(launch, self.f.response)
        self.assertIs(self.t.reservation, reservation)

    def test_reserve_construction_failure(self):
        with patch.object(transfer, 'uuid4', side_effect=RuntimeError('fixture')):
            with self.assertRaises(RuntimeError): self.t.reserve()
        self.assertIsNone(self.m.active)
        self.assertIsNone(self.t.reservation)
