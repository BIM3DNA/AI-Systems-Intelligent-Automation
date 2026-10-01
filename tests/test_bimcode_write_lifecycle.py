"""Provider cleanup probes; fake host evidence only, no event wiring or API."""
import pathlib
import sys
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'AI.extension/lib'))
from bimcode_ai_pane import write_lifecycle as lc
from bimcode_ai_pane import provider_write as m
from bimcode_ai_pane import write_projection as p
from bimcode_ai_pane.write_access import ControlledWritePermission
from bimcode_ai_pane.write_completion import CompletionSink
from bimcode_ai_pane.write_continuation import Coordinator
from test_bimcode_write_leases import setup, request_at
from test_bimcode_write_projection import result
from test_bimcode_write_continuation import response


def fixture(executing=False):
    f, leases, b, identity, admission = setup()
    leases.create_preview(b)
    if executing:
        leases.confirm(b, True); leases.handler_started(b)
    permission = ControlledWritePermission()
    facts = dict(valid_document=True, active_uidocument=True, family_document=False, host_document=True,
                 linked_document=False, workshared=False, read_only=False, modifiable=False,
                 fixed_parameter_available=True, fixed_parameter_binding_valid=True)
    assert permission.enable_from_human('doc1', facts, True)
    sink = CompletionSink(b.owner, lambda value: None)
    coordinator = Coordinator()
    lifecycle = lc.Lifecycle(b.owner, admission, permission, leases, sink, coordinator)
    request = request_at(identity, 'WRITE_EXECUTING' if executing else 'PREVIEW_READY')
    return lifecycle, request, coordinator, f


def finish_host(lifecycle, request, data):
    states = {'MEP_PARAMETER_WRITE_OK': 'WRITE_SUCCEEDED', 'MEP_PARAMETER_WRITE_FAILED': 'WRITE_FAILED',
              'MEP_PARAMETER_WRITE_INDETERMINATE': 'WRITE_INDETERMINATE'}
    receipt = p.freeze_result(data)
    for state in (states[data['classification']], 'HOST_RESULT_READY'):
        step = m.transition(request, request.correlation, state, 1001, 'TEST', host_result=receipt)
        assert step.accepted, step.reason
        request = step.request
    lifecycle.sink.store(data)
    return request


class CleanupTests(unittest.TestCase):
    def test_lifecycle_methods(self):
        for method in ('document_switch', 'document_close', 'pane_disposal', 'shutdown', 'abandon'):
            lifecycle, req, coord, _ = fixture()
            out = getattr(lifecycle, method)(req)
            self.assertTrue(out.owner_released, method)
            self.assertFalse(lifecycle.permission.view_model()['enabled'])
            self.assertEqual(lifecycle.leases.preview.state, 'INVALIDATED')
            self.assertTrue(lifecycle.sink.closed)
            self.assertIsNone(lifecycle.sink.callback)
            self.assertTrue(coord.closed)
            self.assertFalse(lifecycle.sink.deliver('logical1'))
            self.assertIsNone(lifecycle.admission.active)

    def test_idempotence(self):
        lifecycle, req, _, _ = fixture()
        first = lifecycle.document_close(req)
        generation = lifecycle.permission.generation
        self.assertIs(first, lifecycle.document_close(req))
        self.assertEqual(lifecycle.permission.generation, generation)

    def test_owner_cannot_be_stolen(self):
        lifecycle, req, _, _ = fixture()
        lifecycle.admission.release(lifecycle.owner, 'OLD')
        other = lifecycle.admission.acquire('READ_ONLY_PROVIDER_TOOL', 'other', 'other', 'doc2', 'session1', 0)
        generation = lifecycle.permission.generation
        with self.assertRaisesRegex(ValueError, 'LEASE_CORRELATION_FAILED'): lifecycle.document_switch(req)
        self.assertEqual(lifecycle.admission.active, other)
        self.assertEqual(lifecycle.permission.generation, generation)

    def test_wrong_request_no_side_effects(self):
        lifecycle, req, coord, _ = fixture()
        with self.assertRaises(ValueError):
            lifecycle.shutdown(req._replace(correlation=req.correlation._replace(logical_request_id='wrong')))
        self.assertTrue(lifecycle.permission.view_model()['enabled'])
        self.assertFalse(coord.closed)
        self.assertEqual(lifecycle.leases.preview.state, 'ACTIVE')

    def test_active_execution_retains_owner_and_lock(self):
        lifecycle, req, _, _ = fixture(True)
        out = lifecycle.shutdown(req)
        self.assertTrue(out.owner_held); self.assertFalse(out.owner_released)
        self.assertTrue(lifecycle.admission.safety_locked)
        self.assertEqual(lifecycle.admission.active, lifecycle.owner)
        self.assertEqual(lifecycle.leases.queue.state, 'EXECUTION_STARTED')
        self.assertIsNone(out.host_result)  # No fabricated success/failure/rollback.

    def test_handler_admitted_unknown_result_is_conservative(self):
        lifecycle, req, _, _ = fixture(True)
        out = lifecycle.document_close(req._replace(state='WRITE_REQUEST_QUEUED'))
        self.assertTrue(out.owner_held)
        self.assertTrue(out.retained_safety_lock)

    def test_authoritative_completion_after_cleanup_retained(self):
        lifecycle, req, _, _ = fixture(True)
        lifecycle.document_close(req)
        ready = finish_host(lifecycle, req, result())
        out = lifecycle.document_close(ready)
        self.assertTrue(out.owner_released)
        self.assertEqual(out.host_result, ready.host_result)
        self.assertTrue(p.project_receipt(out.host_result)['transaction_committed'])
        self.assertTrue(out.retained_safety_lock)  # Only explicit host inspection can clear.

    def test_indeterminate_retains_safety(self):
        lifecycle, req, _, _ = fixture(True)
        data = result('INDETERMINATE', 'TRANSACTION_PENDING')
        data.update(transaction_started=True, transaction_status='Pending', model_modified=None)
        ready = finish_host(lifecycle, req, data)
        out = lifecycle.pane_disposal(ready)
        self.assertTrue(out.owner_released)
        self.assertTrue(out.retained_safety_lock)
        self.assertEqual(out.host_result, ready.host_result)
        self.assertIsNone(lifecycle.admission.acquire('HUMAN_DEV_WRITE', 'new', 'new', 'doc1', 'session1', 0))

    def test_committed_verification_failure_not_rewritten(self):
        lifecycle, req, _, _ = fixture(True)
        data = result(); data.update(classification='MEP_PARAMETER_WRITE_FAILED', reason_code='VERIFICATION_FAILED', verification_passed=False)
        ready = finish_host(lifecycle, req, data)
        out = lifecycle.document_switch(ready)
        self.assertEqual(p.project_receipt(out.host_result), p.project_receipt(p.freeze_result(data)))

    def test_terminal_continuation_success_and_failure(self):
        for failed in (False, True):
            lifecycle, req, coord, _ = fixture(True)
            ready = finish_host(lifecycle, req, result())
            lifecycle.sink.deliver('logical1')
            snap = coord.begin(ready, lifecycle.sink, lifecycle.admission, 'fake-model', 1002)
            returned = coord.run_worker(snap, lambda *a, **k: {'reason': 'CONTINUATION_TIMEOUT'} if failed else response(snap))
            final = coord.finish(snap, returned, 1003)
            out = lifecycle.continuation_terminal(coord.request)
            self.assertTrue(out.owner_released)
            self.assertEqual(out.host_result, final.host_result)
            self.assertEqual(out.request.provider_status.status, 'FAILED' if failed else 'COMPLETE')
            self.assertIs(out, lifecycle.continuation_terminal(coord.request))

    def test_late_continuation_rejected(self):
        lifecycle, req, coord, _ = fixture(True)
        ready = finish_host(lifecycle, req, result()); lifecycle.sink.deliver('logical1')
        snap = coord.begin(ready, lifecycle.sink, lifecycle.admission, 'fake-model', 1002)
        returned = coord.run_worker(snap, lambda *a, **k: response(snap))
        lifecycle.abandon(coord.request)
        with self.assertRaises(ValueError): coord.finish(snap, returned, 1003)
        self.assertEqual(lifecycle.receipt, ready.host_result)

    def test_terminal_requires_terminal_state(self):
        lifecycle, req, _, _ = fixture()
        with self.assertRaisesRegex(ValueError, 'REQUEST_NOT_TERMINAL'): lifecycle.continuation_terminal(req)

    def test_conflicting_receipt_rejected(self):
        lifecycle, req, _, _ = fixture(True)
        ready = finish_host(lifecycle, req, result())
        wrong = result(); wrong['before_value'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'HOST_RESULT_IMMUTABLE'):
            lifecycle.shutdown(ready._replace(host_result=p.freeze_result(wrong)))

    def test_reenabled_permission_not_disabled_by_stale_cleanup(self):
        lifecycle, req, _, _ = fixture(); lifecycle.document_close(req)
        generation = lifecycle.permission.generation
        lifecycle.permission.disable()
        with self.assertRaisesRegex(ValueError, 'LEASE_CORRELATION_FAILED'): lifecycle.shutdown(req)
        self.assertEqual(lifecycle.permission.generation, generation + 1)

    def test_no_external_event_wiring_or_mutation(self):
        import ast
        for name in ('write_clock', 'write_leases', 'write_lifecycle'):
            tree = ast.parse((ROOT / ('AI.extension/lib/bimcode_ai_pane/' + name + '.py')).read_text())
            attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
            self.assertFalse(attrs & {'Set', 'Transaction', 'Raise', 'Show', 'RegisterDockablePane', 'Add'})

    def test_closed_runtime_source_identical(self):
        import subprocess
        paths = ['AI.extension/lib/bimcode_write_execution.py', 'AI.extension/lib/bimcode_write_runtime.py',
                 'AI.extension/lib/bimcode_ai_pane/write_coordinator.py', 'AI.extension/lib/bimcode_ai_pane/write_continuation.py',
                 'AI.extension/lib/bimcode_ai_pane/lifecycle.py', 'AI.extension/lib/bimcode_ai_pane/ai_tool_registry.py',
                 'AI.extension/lib/prompt_catalog.json', 'AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py']
        baseline = 'b703acaa143c5a834f35184001ef1b1b8c8228ca'
        for path in paths:
            old = subprocess.check_output(['git', 'show', baseline + ':' + path])
            self.assertEqual(old.replace(b'\r\n', b'\n'), (ROOT / path).read_bytes().replace(b'\r\n', b'\n'), path)
