"""Lossless admission cleanup; real manager, no host API or network."""
import sys
import pathlib
import unittest
import threading
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'AI.extension/lib'))
from bimcode_ai_pane.write_access import OperationAdmission


class Safety(unittest.TestCase):
    def setUp(self):
        self.manager = OperationAdmission()
        self.owner = self.manager.acquire('HUMAN_DEV_WRITE', 'r', 'h', 'd', 's', 1)
        self.source = object()

    def test_unresolved_cleanup_is_lossless_under_contention(self):
        m = self.manager
        m._lock.acquire(False)
        try:
            self.assertFalse(m.cleanup(self.owner, 'DOCUMENT_CLOSE', transaction_unresolved=True))
            self.assertTrue(m.safety_locked)
        finally:
            m._lock.release()
        self.assertFalse(m.release(self.owner, 'ORDINARY_FINALIZATION'))
        self.assertIsNone(m.acquire('HUMAN_DEV_WRITE', 'r2', 'h2', 'd', 's', 2))

    def defer(self, active=False, unresolved=True):
        m = self.manager
        m._lock.acquire(False)
        try:
            self.assertFalse(m.cleanup(self.owner, 'PANE_DISPOSAL', active, unresolved,
                                       evidence_source=self.source))
        finally:
            m._lock.release()

    def test_inspection_and_explicit_reconciliation(self):
        self.defer()
        snapshot = self.manager.inspect_safety()
        for key, value in dict(retained_safety_lock=True, pending_cleanup=True,
                cleanup_reason='PANE_DISPOSAL', pending_cleanup_execution_active=False,
                requires_intervention=True, owner_present=True, owner_state='HELD').items():
            self.assertEqual(snapshot[key], value)
        self.assertTrue(self.manager.reconcile_cleanup(self.owner, True))
        self.assertIsNone(self.manager.active)
        self.assertTrue(self.manager.safety_locked)
        self.assertFalse(self.manager.inspect_safety()['pending_cleanup'])
        self.assertFalse(self.manager.resolve_safety(False))
        ticket = self.manager.resolution_ticket(self.source, self.owner)
        self.assertTrue(self.manager.resolve_safety(True, ticket))

    def test_executing_owner_needs_quiescent_attestation(self):
        self.defer(active=True)
        self.assertFalse(self.manager.reconcile_cleanup(self.owner))
        self.assertFalse(self.manager.cleanup(self.owner, 'ABANDONED'))
        self.assertIs(self.manager.active, self.owner)
        self.assertTrue(self.manager.reconcile_cleanup(self.owner, True))
        self.assertTrue(self.manager.safety_locked)

    def test_unrelated_release_and_resolution_cannot_clear(self):
        self.defer()
        other = self.owner._replace(token='other')
        self.assertFalse(self.manager.release(other, 'LATE'))
        self.assertFalse(self.manager.reconcile_cleanup(other, True))
        self.assertFalse(self.manager.resolve_safety(True))
        self.manager.retain_safety(False)
        self.assertTrue(self.manager.safety_locked)

    def test_normal_cleanup_does_not_create_safety_lock(self):
        self.assertTrue(self.manager.cleanup(self.owner, 'REQUEST_FINALIZED'))
        self.assertFalse(self.manager.safety_locked)

    def test_public_owner_cannot_bypass_admission(self):
        with self.assertRaises(AttributeError):
            self.manager.active = None

    def test_success_evidence_cannot_erase_unresolved_evidence(self):
        self.manager.retain_safety()
        self.manager.retain_safety(False)
        self.assertTrue(self.manager.safety_locked)
        self.assertTrue(self.manager.release(self.owner, 'COMPLETE'))
        self.assertTrue(self.manager.safety_locked)

    def test_concurrent_cleanup_release_preserves_evidence(self):
        for unused in range(30):
            self.setUp()
            barrier = threading.Barrier(2)
            def cleanup():
                barrier.wait()
                self.manager.cleanup(self.owner, 'DOCUMENT_CLOSE', transaction_unresolved=True)
            thread = threading.Thread(target=cleanup); thread.start()
            barrier.wait(); self.manager.release(self.owner, 'DONE')
            thread.join(2); self.assertFalse(thread.is_alive())
            self.assertTrue(self.manager.safety_locked)

    def test_reentrant_cleanup_during_acquire_publication(self):
        self.manager.release(self.owner, 'DONE')
        from bimcode_ai_pane import write_access
        original = write_access.uuid4
        def intent():
            self.manager.cleanup(self.owner, 'DOCUMENT_CLOSE', transaction_unresolved=True)
            return original()
        with patch.object(write_access, 'uuid4', side_effect=intent):
            self.assertIsNone(self.manager.acquire('HUMAN_DEV_WRITE', 'r2', 'h2', 'd', 's', 2))
        self.assertTrue(self.manager.safety_locked)


class TransferSafety(unittest.TestCase):
    def setUp(self):
        from test_bimcode_provider_write_transfer import TransferTests
        self.fixture = TransferTests(); self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.f = self.fixture
        self.f.reserve()

    def test_cleanup_during_transfer_from_other_thread(self):
        from bimcode_ai_pane import provider_write_transfer
        f = self.f; owner = f.m.active; original = provider_write_transfer.uuid4
        def concurrent_intent():
            thread = threading.Thread(target=lambda: f.m.cleanup(owner, 'DOCUMENT_CLOSE', transaction_unresolved=True))
            thread.start(); thread.join(2); self.assertFalse(thread.is_alive())
            return original()
        with patch.object(provider_write_transfer, 'uuid4', side_effect=concurrent_intent):
            with self.assertRaises(ValueError): f.t.transfer()
        self.assertIs(f.m.active, owner)
        self.assertIsNone(f.t.transferred)
        self.assertTrue(f.m.inspect_safety()['pending_cleanup'])

    def test_late_predecessor_cleanup_matches_transferred_owner(self):
        f = self.f; old = f.m.active; f.t.transfer()
        self.assertTrue(f.m.cleanup(old, 'DOCUMENT_CLOSE', transaction_unresolved=True))
        self.assertIsNone(f.m.active)
        self.assertTrue(f.m.safety_locked)
        with self.assertRaises(ValueError): f.t.adopt()

    def test_document_and_pane_invalidation_deferred_and_observable(self):
        f = self.f
        f.m._lock.acquire(False)
        try:
            f.s.write_gate.cleanup('PANE_DISPOSAL')
            self.assertTrue(f.m.inspect_safety()['pending_cleanup'])
            self.assertTrue(f.t.invalidated)
        finally: f.m._lock.release()
        with self.assertRaises(ValueError): f.t.transfer()
        self.assertFalse(f.m.release(f.m.active, 'ORDINARY'))
        f.s.write_gate.cleanup('DOCUMENT_CLOSE')
        self.assertIsNone(f.m.active)
        self.assertFalse(f.m.inspect_safety()['pending_cleanup'])
        self.assertFalse(f.m.safety_locked)


if __name__ == '__main__':
    unittest.main()
