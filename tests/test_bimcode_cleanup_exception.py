"""FIX-003 cleanup exception boundary; actual admission, no Revit/network."""
import unittest
from types import SimpleNamespace as N
from unittest.mock import Mock
from test_bimcode_admission_safety import OperationAdmission
from bimcode_ai_pane.session_write_gate import SessionWriteGate


class CleanupException(unittest.TestCase):
    def setUp(self):
        self.m = OperationAdmission()
        self.owner = self.m.acquire('HUMAN_DEV_WRITE', 'r', 'h', 'd', 's', 1)
        self.gate = SessionWriteGate(self.m)

    def fail(self):
        self.gate.lifecycle = N(cleanup=Mock(side_effect=ValueError('missing evidence')))
        self.gate.cleanup('PANE_DISPOSAL')

    def test_valid_owner_still_records_unknown_evidence(self):
        self.gate.lifecycle = N(owner=self.owner, cleanup=Mock(side_effect=ValueError()))
        self.gate.cleanup('SHUTDOWN')
        self.assertIsNone(self.m.resolution_ticket(self.gate, self.owner))
        self.assertTrue(self.m.safety_locked)

    def test_owner_getter_is_never_read(self):
        class Broken(object):
            @property
            def owner(self):
                raise AssertionError('owner must not be read')
            def cleanup(self, *args):
                raise ValueError()
        self.gate.lifecycle = Broken()
        self.gate.cleanup('SHUTDOWN')
        self.assertTrue(self.m.safety_locked)

    def test_malformed_lifecycle(self):
        self.gate.lifecycle = object()
        self.gate.cleanup('SHUTDOWN')
        self.assertTrue(self.m.safety_locked)

    def test_secondary_failures_follow_publication(self):
        def broken(*args):
            self.assertTrue(self.m.safety_locked)
            raise AttributeError('secondary')
        leases, sink, continuation = Mock(), Mock(), Mock()
        leases.invalidate.side_effect = broken
        sink.cleanup.side_effect = broken
        continuation.close.side_effect = broken
        self.gate.lifecycle = N(cleanup=Mock(side_effect=ValueError()),
                                leases=leases, sink=sink, continuation=continuation)
        self.gate.cleanup('SHUTDOWN')
        leases.invalidate.assert_called_once_with('SHUTDOWN')
        sink.cleanup.assert_called_once_with()
        continuation.close.assert_called_once_with('cancelled')

    def test_prior_evidence_generation_and_stale_ticket(self):
        source = object()
        self.m.retain_safety(True, source, self.owner, 'prior')
        ticket = self.m.resolution_ticket(source, self.owner)
        before = self.m.inspect_safety()
        self.fail()
        after = self.m.inspect_safety()
        self.assertEqual(after['safety_evidence_generation'], before['safety_evidence_generation'] + 1)
        self.assertEqual(after['safety_evidence_count'], 2)
        self.m.release(self.owner, 'DONE')
        self.assertFalse(self.m.resolve_safety(True, ticket))
        ticket = self.m.resolution_ticket(source, self.owner)
        self.m.resolve_safety(True, ticket)
        self.assertTrue(self.m.safety_locked)

    def test_duplicate_cleanup_deduplicates(self):
        self.fail()
        before = self.m.inspect_safety()
        self.gate.cleanup('SHUTDOWN')
        self.assertEqual(before, self.m.inspect_safety())

    def test_overflow_remains_fail_closed(self):
        for unused in range(20):
            self.m.retain_safety(True)
        self.fail()
        state = self.m.inspect_safety()
        self.assertTrue(state['safety_evidence_overflow'])
        self.assertEqual(state['safety_evidence_count'], 16)
        self.assertFalse(self.m.resolve_safety(True))

    def test_contended_pending_cleanup_preserved(self):
        self.m._lock.acquire(False)
        try:
            self.m.cleanup(self.owner, 'DOCUMENT_CLOSE', execution_active=True)
            self.fail()
            self.assertTrue(self.m.inspect_safety()['pending_cleanup'])
            self.assertIs(self.m.active, self.owner)
        finally:
            self.m._lock.release()

    def test_reentrant_state_lock_publication(self):
        with self.m._state_lock:
            self.fail()
            self.assertTrue(self.m.safety_locked)

    def test_release_cannot_clear_or_admit(self):
        self.fail()
        self.m.release(self.owner, 'DONE')
        self.assertTrue(self.m.safety_locked)
        self.assertIsNone(self.m.acquire('HUMAN_DEV_WRITE', 'r2', 'h2', 'd', 's', 2))

    def test_inspection_is_pure(self):
        self.fail()
        before = self.m.inspect_safety()
        for unused in range(3):
            self.assertEqual(before, self.m.inspect_safety())

    def test_missing_owner_retains_safety(self):
        self.gate.lifecycle = N(cleanup=Mock(side_effect=ValueError('missing evidence')))
        self.gate.cleanup('PANE_DISPOSAL')
        self.assertTrue(self.m.safety_locked)
        self.assertIs(self.m.active, self.owner)
        self.assertGreater(self.m.inspect_safety()['safety_evidence_generation'], 0)


if __name__ == '__main__':
    unittest.main()
