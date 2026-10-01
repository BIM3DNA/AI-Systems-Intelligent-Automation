"""Deterministic provider-only clock/lease tests; no Revit or provider calls."""
import json
import pathlib
import sys
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'AI.extension/lib'))
from bimcode_ai_pane.write_clock import Clock, deadline
from bimcode_ai_pane import write_leases as l
from bimcode_ai_pane import provider_write as m
from bimcode_ai_pane import write_projection as p
from bimcode_ai_pane.write_access import OperationAdmission
from bimcode_ai_pane.write_completion import CompletionSink
from bimcode_ai_pane.write_continuation import Coordinator


class FakeTime(object):
    def __init__(self):
        self.now, self.utc = 1000.0, '2026-10-01T12:00:00Z'
        self.clock = Clock(lambda: self.now, lambda: self.utc)

    def advance(self, seconds):
        self.now += seconds


def setup():
    fake = FakeTime()
    identity = m.correlation('logical1', 'host1', 'session1', 'doc1', 'resp1', 'call1', 'New')
    admission = OperationAdmission()
    owner = admission.acquire('CONTROLLED_WRITE_PROVIDER_TOOL', 'logical1', 'host1', 'doc1', 'session1', 0)
    context = l.binding(identity, owner, 'fingerprint', 123, 'unique1', False, None, 1, 2)
    return fake, l.Leases(fake.clock), context, identity, admission


def request_at(identity, state):
    request = m.new_request(identity, 0)
    path = ('PROVIDER_INITIAL_REQUEST', 'PROVIDER_TOOL_SELECTED', 'WRITE_ARGUMENTS_VALIDATED',
            'HOST_PREVIEW_BUILDING', 'PREVIEW_READY', 'AWAITING_HUMAN_CONFIRMATION',
            'WRITE_REQUEST_QUEUED', 'WRITE_EXECUTING')
    for index, target in enumerate(path):
        step = m.transition(request, identity, target, index + 1, 'TEST')
        assert step.accepted, step.reason
        request = step.request
        if target == state: return request
    raise ValueError(state)


class Clocks(unittest.TestCase):
    def test_fake_advance(self):
        f = FakeTime(); self.assertEqual(f.clock.sample().monotonic, 1000)
        f.advance(120); self.assertEqual(f.clock.sample().monotonic, 1120)

    def test_real_monotonic(self):
        clock = Clock(); first = clock.sample(); second = clock.sample()
        self.assertGreaterEqual(second.monotonic, first.monotonic)
        self.assertTrue(second.utc.endswith('Z'))

    def test_bad_duration(self):
        for value in (-1, 0, float('nan'), float('inf'), True):
            with self.assertRaises(ValueError): deadline(1, value)

    def test_regression_poison(self):
        f = FakeTime(); f.clock.sample(); f.advance(-1)
        with self.assertRaisesRegex(ValueError, 'CLOCK_STATE_INVALID'): f.clock.sample()
        f.advance(20)
        with self.assertRaises(ValueError): f.clock.sample()

    def test_bad_clock_values(self):
        for value in (-1, float('nan'), float('inf'), True, None):
            with self.assertRaises(ValueError): Clock(lambda: value, lambda: 'UTC').sample()

    def test_supplier_exception_and_partial_injection(self):
        with self.assertRaises(ValueError): Clock(lambda: 1)
        with self.assertRaisesRegex(ValueError, 'CLOCK_STATE_INVALID'):
            Clock(lambda: 1 / 0, lambda: 'UTC').sample()


class Preview(unittest.TestCase):
    def test_not_started_and_delay(self):
        f, leases, b, _, _ = setup()
        self.assertEqual(leases.preview.state, 'NOT_STARTED')
        self.assertEqual(leases.check('PREVIEW', b).reason, 'LEASE_NOT_ACTIVE')
        f.advance(10000)
        self.assertTrue(leases.create_preview(b).accepted)
        self.assertEqual(leases.preview.created_at, 11000)
        self.assertEqual(leases.preview.expires_at, 11120)

    def test_preview_boundaries(self):
        for age, accepted in ((119.999, True), (120, False), (120.001, False)):
            f, leases, b, _, _ = setup(); leases.create_preview(b); f.advance(age)
            out = leases.check('PREVIEW', b)
            self.assertEqual(out.accepted, accepted)
            if not accepted: self.assertEqual(out.reason, 'PREVIEW_LEASE_EXPIRED')

    def test_wall_clock_not_authority(self):
        f, leases, b, _, _ = setup(); leases.create_preview(b)
        for wall in ('1900-01-01T00:00:00Z', '2999-01-01T00:00:00Z'):
            f.utc = wall; self.assertTrue(leases.check('PREVIEW', b).accepted)
        f.advance(120); self.assertEqual(leases.check('PREVIEW', b).reason, 'PREVIEW_LEASE_EXPIRED')

    def test_confirm_consumes_without_renewal(self):
        f, leases, b, _, _ = setup(); leases.create_preview(b); f.advance(119)
        self.assertTrue(leases.confirm(b, True).accepted)
        self.assertEqual(leases.preview.state, 'CONSUMED')
        self.assertEqual(leases.queue.created_at, 1119)
        self.assertEqual(leases.queue.expires_at, 1149)
        self.assertEqual(leases.confirm(b, True).reason, 'LEASE_ALREADY_CONSUMED')
        self.assertFalse(leases.create_preview(b).accepted)

    def test_confirm_expired(self):
        f, leases, b, _, _ = setup(); leases.create_preview(b); f.advance(120)
        self.assertEqual(leases.confirm(b, True).reason, 'PREVIEW_LEASE_EXPIRED')
        self.assertEqual(leases.queue.state, 'NOT_STARTED')

    def test_cancel_invalidates(self):
        _, leases, b, _, _ = setup(); leases.create_preview(b)
        self.assertEqual(leases.confirm(b).reason, 'PREVIEW_LEASE_INVALIDATED')
        self.assertFalse(leases.confirm(b, True).accepted)

    def test_every_context_field_bound(self):
        for field in l.Binding._fields:
            _, leases, b, _, _ = setup(); leases.create_preview(b)
            out = leases.check('PREVIEW', b._replace(**{field: 'changed'}))
            self.assertEqual(out.reason, 'LEASE_CORRELATION_FAILED', field)
            self.assertEqual(leases.preview.state, 'INVALIDATED')
            self.assertFalse(leases.check('PREVIEW', b).accepted)

    def test_all_invalidations(self):
        for trigger in l.INVALIDATIONS:
            _, leases, b, _, _ = setup(); leases.create_preview(b); leases.invalidate(trigger)
            self.assertEqual(leases.preview.invalidation, trigger)
            self.assertFalse(leases.confirm(b, True).accepted)

    def test_clock_regression_invalidates_both(self):
        f, leases, b, _, _ = setup(); leases.create_preview(b); f.advance(-1)
        self.assertEqual(leases.check('PREVIEW', b).reason, 'CLOCK_STATE_INVALID')
        self.assertEqual(leases.preview.state, 'INVALIDATED')
        self.assertEqual(leases.queue.state, 'INVALIDATED')

    def test_provenance_deterministic(self):
        _, leases, b, _, _ = setup(); leases.create_preview(b)
        encoded = leases.provenance()
        self.assertEqual(encoded, leases.provenance())
        self.assertEqual(json.loads(encoded)['preview']['created_utc'], '2026-10-01T12:00:00Z')
        self.assertEqual(json.loads(encoded)['preview']['binding']['parameter_guid'], l.c.M4A_TEST_PARAMETER_GUID)

    def test_invalid_binding(self):
        for key, value in (('parameter_guid', 'other'), ('before_value', object()), ('target_element_id', True),
                            ('model_epoch', -1), ('proposed_value', 'bad!')):
            _, leases, b, _, _ = setup()
            self.assertFalse(leases.create_preview(b._replace(**{key: value})).accepted)


class Queue(unittest.TestCase):
    def test_queue_boundaries(self):
        for age, accepted in ((29.999, True), (30, False), (30.001, False)):
            f, leases, b, _, _ = setup(); leases.create_preview(b); f.advance(100); leases.confirm(b, True); f.advance(age)
            out = leases.handler_started(b)
            self.assertEqual(out.accepted, accepted)
            self.assertEqual(leases.queue.created_at, 1100)
            if not accepted: self.assertEqual(out.reason, 'EXECUTION_QUEUE_LEASE_EXPIRED')

    def test_raised_time_and_single_handler(self):
        f, leases, b, _, _ = setup(); leases.create_preview(b); leases.confirm(b, True); f.advance(1)
        self.assertTrue(leases.queue_raised(b).accepted)
        self.assertFalse(leases.queue_raised(b).accepted)
        f.advance(1); self.assertTrue(leases.handler_started(b).accepted)
        self.assertEqual(leases.queue.queue_raised_at, 1001)
        self.assertEqual(leases.queue.handler_started_at, 1002)
        self.assertTrue(leases.queue.consumed)
        self.assertEqual(leases.handler_started(b).reason, 'LEASE_ALREADY_CONSUMED')

    def test_no_retry_expired_queue(self):
        f, leases, b, _, _ = setup(); leases.create_preview(b); leases.confirm(b, True); f.advance(30)
        self.assertFalse(leases.queue_raised(b).accepted)
        self.assertFalse(leases.handler_started(b).accepted)
        self.assertFalse(leases.confirm(b, True).accepted)

    def test_changed_document_owner_epoch(self):
        for field in ('document_id', 'owner', 'model_epoch', 'write_epoch'):
            _, leases, b, _, _ = setup(); leases.create_preview(b); leases.confirm(b, True)
            self.assertEqual(leases.handler_started(b._replace(**{field: 'wrong'})).reason, 'LEASE_CORRELATION_FAILED')
            self.assertEqual(leases.queue.state, 'INVALIDATED')

    def test_after_handler_no_lease_expiry_claim(self):
        f, leases, b, _, _ = setup(); leases.create_preview(b); leases.confirm(b, True); leases.handler_started(b)
        f.advance(300); leases.invalidate('SHUTDOWN')
        self.assertEqual(leases.queue.state, 'EXECUTION_STARTED')
        self.assertEqual(leases.check('EXECUTION_QUEUE', b).reason, 'LEASE_ALREADY_CONSUMED')


class ExpiryIntegration(unittest.TestCase):
    def test_both_expiry_paths_and_continuation(self):
        for state in ('PREVIEW_READY', 'AWAITING_HUMAN_CONFIRMATION', 'WRITE_REQUEST_QUEUED'):
            f, leases, b, identity, adm = setup(); leases.create_preview(b)
            request = request_at(identity, state)
            queue = state == 'WRITE_REQUEST_QUEUED'
            if queue: leases.confirm(b, True)
            f.advance(30 if queue else 120)
            leases.check('EXECUTION_QUEUE' if queue else 'PREVIEW', b)
            ready = l.expired_request(request, leases)
            host = p.project_receipt(ready.host_result)
            self.assertEqual(ready.state, 'HOST_RESULT_READY'); self.assertEqual(ready.terminal_intent, 'EXPIRED')
            for flag in ('transaction_started', 'transaction_committed', 'model_modified', 'verification_performed'):
                self.assertIs(host[flag], False)
            self.assertEqual(host['classification'], 'MEP_PARAMETER_WRITE_NOT_READY')
            self.assertEqual(host['reason_code'], 'EXECUTION_QUEUE_LEASE_EXPIRED' if queue else 'PREVIEW_LEASE_EXPIRED')
            sink = CompletionSink(b.owner); sink.store(host); sink.deliver(identity.logical_request_id)
            coordinator = Coordinator(); snap = coordinator.begin(ready, sink, adm, 'fake-model', f.now)
            returned = coordinator.run_worker(snap, lambda *a, **k: {'reason': 'CONTINUATION_TIMEOUT'})
            out = coordinator.finish(snap, returned, f.now)
            self.assertEqual(coordinator.request.state, 'EXPIRED'); self.assertEqual(out.host_result, ready.host_result)
            with self.assertRaises(ValueError): l.expired_request(request, leases)

    def test_mismatch_and_executing_rejected(self):
        f, leases, b, identity, _ = setup(); leases.create_preview(b); f.advance(120); leases.check('PREVIEW', b)
        req = request_at(identity, 'PREVIEW_READY')
        with self.assertRaises(ValueError): l.expired_request(req._replace(correlation=identity._replace(logical_request_id='wrong')), leases)
        with self.assertRaises(ValueError): l.expired_request(req._replace(state='WRITE_EXECUTING'), leases)

    def test_legacy_reason_still_accepted(self):
        from test_bimcode_provider_write import Machine, PREFIX, CONFIRM, TAIL
        from test_bimcode_write_projection import result
        req = Machine().run_path(PREFIX + CONFIRM[:2] + ('APPROVAL_EXPIRED',) + TAIL + ('EXPIRED',), result('NOT_READY', 'CONFIRMATION_EXPIRED'))
        self.assertEqual(req.state, 'EXPIRED')
