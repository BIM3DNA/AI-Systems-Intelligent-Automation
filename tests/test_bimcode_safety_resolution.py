"""FIX-002 safety evidence correlation and pure retained inspection."""
import unittest
import json
from types import SimpleNamespace as N
from unittest.mock import Mock, patch
from test_bimcode_admission_safety import OperationAdmission
import test_bimcode_provider_write_handoff as handoff_tests


class Reproductions(unittest.TestCase):
    def test_stale_resolution_rejected(self):
        m = OperationAdmission()
        owner = m.acquire('HUMAN_DEV_WRITE', 'r', 'h', 'd', 's', 1)
        m.cleanup(owner, 'DOCUMENT_CLOSE', transaction_unresolved=True)
        # Before FIX-002 there is no generation/ticket: True alone clears all.
        generation = getattr(m, '_safety_generation', None)
        m.retain_safety(True)
        self.assertFalse(m.resolve_safety(True, generation) if generation is not None
                         else m.resolve_safety(True))
        self.assertTrue(m.safety_locked)

    def test_inspection_does_not_expire_continuation(self):
        f = handoff_tests.HandoffTests(); f.setUp()
        self.addCleanup(f.doCleanups)
        f.finish()
        pending = f.h.pending
        request = f.f.d.request
        f.f.now += 121
        for unused in range(2):
            state = json.loads(f.s.controlled_writes.inspect())
            self.assertTrue(state['continuation']['pending'])
            self.assertIs(f.h.pending, pending)
            self.assertIs(f.f.d.request, request)
        f.h.check()
        self.assertIsNone(f.h.pending)


class Evidence(unittest.TestCase):
    def setUp(self):
        self.m = OperationAdmission()
        self.owner = self.m.acquire('HUMAN_DEV_WRITE', 'r', 'h', 'd', 's', 1)
        self.source = object()
        self.m.retain_safety(True, self.source, self.owner, 'first')

    def ticket(self):
        return self.m.resolution_ticket(self.source, self.owner)

    def release(self):
        self.assertTrue(self.m.release(self.owner, 'DONE'))

    def test_matching_evidence(self):
        t = self.ticket(); self.release()
        self.assertTrue(self.m.resolve_safety(True, t))
        self.assertFalse(self.m.safety_locked)

    def test_new_evidence_rejects_retained_ticket(self):
        t = self.ticket(); self.release()
        self.m.retain_safety(True, self.source, self.owner, 'second')
        self.assertFalse(self.m.resolve_safety(True, t))
        self.assertTrue(self.m.safety_locked)

    def test_generation_alone_not_authority(self):
        t = self.ticket(); self.release()
        for value in (t.generation, t._asdict(), t._replace(generation=t.generation+1), True):
            self.assertFalse(self.m.resolve_safety(True, value))

    def test_active_owner(self):
        self.assertFalse(self.m.resolve_safety(True, self.ticket()))

    def test_pending_cleanup(self):
        self.m._lock.acquire(False)
        try: self.m.cleanup(self.owner, 'PANE_DISPOSAL', transaction_unresolved=True, evidence_source=self.source)
        finally: self.m._lock.release()
        t = self.ticket()
        self.assertFalse(self.m.resolve_safety(True, t))
        self.assertTrue(self.m.reconcile_cleanup(self.owner, True))
        self.assertTrue(self.m.resolve_safety(True, t))

    def test_quiescence_required(self):
        t = self.ticket(); self.release()
        for value in (False, None, 1): self.assertFalse(self.m.resolve_safety(value, t))

    def test_wrong_request(self):
        self.assertIsNone(self.m.resolution_ticket(self.source, self.owner._replace(token='other')))

    def test_wrong_executor(self):
        self.assertIsNone(self.m.resolution_ticket(object(), self.owner))

    def test_multiple_sources_resolved_independently(self):
        other = object()
        self.m.retain_safety(True, other, self.owner, 'other')
        self.release()
        self.assertTrue(self.m.resolve_safety(True, self.ticket()))
        self.assertTrue(self.m.safety_locked)
        self.assertTrue(self.m.resolve_safety(True, self.m.resolution_ticket(other, self.owner)))
        self.assertFalse(self.m.safety_locked)

    def test_cleanup_retry_deduplicated(self):
        self.m._lock.acquire(False)
        try:
            self.m.cleanup(self.owner, 'DOCUMENT_CLOSE', True, True, self.source)
            generation = self.m.inspect_safety()['safety_evidence_generation']
            for reason in ('DOCUMENT_CLOSE', 'PANE_DISPOSAL', 'SHUTDOWN'):
                self.m.cleanup(self.owner, reason, True, True, self.source)
                self.assertEqual(self.m.inspect_safety()['safety_evidence_generation'], generation)
        finally: self.m._lock.release()
        self.m.reconcile_cleanup(self.owner, True)
        self.assertTrue(self.m.safety_locked)

    def test_generation_survives_successful_resolution(self):
        t = self.ticket(); self.release(); self.m.resolve_safety(True, t)
        self.m.retain_safety(True, self.source, self.owner, 'first')
        self.assertGreater(self.m.inspect_safety()['safety_evidence_generation'], t.generation)
        self.assertFalse(self.m.resolve_safety(True, t))

    def test_unknown_source_requires_intervention(self):
        self.m.retain_safety()
        self.release(); self.m.resolve_safety(True, self.ticket())
        self.assertTrue(self.m.safety_locked)
        self.assertIsNone(self.m.resolution_ticket(None, self.owner))

    def test_bounded_overflow_never_clears(self):
        for i in range(20): self.m.retain_safety(True, self.source, self.owner, str(i))
        snapshot = self.m.inspect_safety()
        self.assertEqual(snapshot['safety_evidence_count'], 16)
        self.assertTrue(snapshot['safety_evidence_overflow'])
        self.assertIsNone(self.ticket())

    def test_reentrant_resolution_rejected(self):
        t = self.ticket(); self.release()
        self.m._lock.acquire(False)
        try: self.assertFalse(self.m.resolve_safety(True, t))
        finally: self.m._lock.release()
        self.assertTrue(self.m.safety_locked)

    def test_owner_and_pending_snapshot_are_not_execution_claim(self):
        before = self.m.inspect_safety()
        self.assertTrue(before['owner_present'])
        self.assertEqual(before['owner_state'], 'HELD')
        self.assertNotIn('execution_active', before)
        before['owner_identity']['token'] = 'forged'
        self.assertEqual(self.m.inspect_safety()['owner_identity']['token'], self.owner.token)
        self.release()
        self.assertEqual(self.m.inspect_safety()['owner_state'], 'QUIESCENT')


class RecoveryCaller(unittest.TestCase):
    def run_recovery(self, newer=False):
        import test_bimcode_write_admission as fixtures
        f = fixtures.Integration(); f.setUp(); self.addCleanup(f.doCleanups)
        c = f.coordinator; m = c.admission
        c.owner = fixtures.acquire(m)
        m.retain_safety(True, c.executor, c.owner, 'HOST_RESULT_UNRESOLVED')
        m.release(c.owner, 'DONE')
        c.resolving = True; c.executor.retained = object()
        def query(*unused):
            c.executor.retained = None
            if newer: m.retain_safety(True, object(), c.owner, 'NEW_OTHER_SOURCE')
            return fixtures.result()
        c.executor.check_pending = Mock(side_effect=query)
        c.output = Mock()
        f.module.framework.Guid = N(Parse=lambda value: value)
        c.execute(None)
        c.executor.check_pending.assert_called_once()
        return m

    def test_existing_host_recovery_correlated(self):
        self.assertFalse(self.run_recovery().safety_locked)

    def test_new_evidence_during_host_query_preserved(self):
        self.assertTrue(self.run_recovery(True).safety_locked)


if __name__ == '__main__':
    unittest.main()
