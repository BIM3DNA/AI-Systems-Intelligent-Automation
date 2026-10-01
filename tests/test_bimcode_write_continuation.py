"""Offline continuation authority, protocol, lifecycle and mocked SDK probes."""
import json
import pathlib
import sys
import unittest
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'AI.extension/lib'))
sys.path.insert(0, str(ROOT / 'BIMCode_Provider'))
from bimcode_ai_pane import write_continuation as c
from bimcode_ai_pane import provider_write as m
from bimcode_ai_pane import write_projection as p
from bimcode_ai_pane.write_access import OperationAdmission
from bimcode_ai_pane.write_completion import CompletionSink
from test_bimcode_write_projection import result
from test_bimcode_provider_write import PREFIX, CONFIRM
import write_tool_protocol as wire
import provider
import protocol


def fixture(data=None, states=None):
    data = data or result()
    identity = m.correlation('logical1', 'host1', 'session1', 'doc1', 'resp1', 'call1', 'New')
    request = m.new_request(identity, 0)
    receipt = p.freeze_result(data)
    outcome = {'MEP_PARAMETER_WRITE_OK': 'WRITE_SUCCEEDED', 'MEP_PARAMETER_WRITE_FAILED': 'WRITE_FAILED',
               'MEP_PARAMETER_WRITE_INDETERMINATE': 'WRITE_INDETERMINATE'}
    states = states or PREFIX + CONFIRM + (outcome[data['classification']], 'HOST_RESULT_READY')
    for i, state in enumerate(states):
        step = m.transition(request, identity, state, i + 1, 'TEST',
                    host_result=receipt if state in tuple(outcome.values()) + ('HOST_RESULT_READY',) else None)
        assert step.accepted, step.reason
        request = step.request
    admission = OperationAdmission()
    owner = admission.acquire('CONTROLLED_WRITE_PROVIDER_TOOL', 'logical1', 'host1', 'doc1', 'session1', 0)
    sink = CompletionSink(owner)
    sink.store(data)
    sink.deliver('logical1')
    return request, sink, admission


def response(snapshot, **changes):
    data = dict(protocol_version=1, request_id=snapshot.transport_id, ok=True, provider='openai',
                model='fake-model', text='A non-authoritative explanation.', error=None, state='WRITE_FINAL',
                response_id='resp_final', previous_response_id='resp1', call_id='call1')
    data.update(changes)
    return data


class Continuation(unittest.TestCase):
    def begin(self, data=None, states=None):
        coordinator = c.Coordinator()
        request, sink, admission = fixture(data, states)
        snapshot = coordinator.begin(request, sink, admission, 'fake-model', 20)
        return coordinator, snapshot

    def finish(self, coord, snapshot, data):
        returned = coord.run_worker(snapshot, lambda payload, decoder: data)
        return coord.finish(snapshot, returned, 21)

    def test_payload_exact(self):
        coord, snap = self.begin()
        envelope = c.payload(snap)
        self.assertEqual(protocol.parse(json.dumps(envelope)), envelope)
        payload = wire.final_payload(envelope)
        self.assertFalse(payload['store'])
        self.assertEqual(payload['tools'], [])
        self.assertEqual(payload['tool_choice'], 'none')
        self.assertEqual(payload['previous_response_id'], 'resp1')
        self.assertEqual(payload['input'], [dict(type='function_call_output', call_id='call1', output=snap.host_result.json)])
        self.assertFalse(payload['parallel_tool_calls'])
        self.assertEqual(snap.function_call_output, snap.host_result.json)
        with self.assertRaises(AttributeError):
            snap.host_reason = 'changed'

    def test_missing_ids(self):
        for key in ('previous_response_id', 'call_id'):
            for value in (None, '', 'a' * 257, 'bad\n'):
                req, sink, admission = fixture()
                req = req._replace(correlation=req.correlation._replace(**{key: value}))
                with self.assertRaises(ValueError):
                    c.Coordinator().begin(req, sink, admission, 'fake-model', 20)

    def test_wire_bad_inputs(self):
        _, snap = self.begin()
        for key, val in (('call_id', ''), ('previous_response_id', None), ('tool_name', 'arbitrary'),
                         ('function_call_output', 'x' * 80001), ('function_call_output', '{"x":NaN}'),
                         ('function_call_output', {'object': object()})):
            data = c.payload(snap); data[key] = val
            with self.assertRaises((ValueError, TypeError)):
                wire.final_payload(data)

    def test_success_and_cleanup(self):
        coord, snap = self.begin()
        out = self.finish(coord, snap, response(snap))
        self.assertEqual(out.provider_status.status, 'COMPLETE')
        self.assertEqual(out.host_result, snap.host_result)
        self.assertEqual(coord.request.state, 'COMPLETED')
        self.assertEqual([v[1] for v in coord.request.history[-3:]],
                         ['PROVIDER_CONTINUATION_PENDING', 'PROVIDER_FINAL_RESPONSE_READY', 'COMPLETED'])
        self.assertTrue(dict(out.cleanup)['callback_invalidation_required'])
        self.assertTrue(out.tools_disabled)

    def test_transport_failures(self):
        for code, reason in (('SIDECAR_TIMEOUT', 'CONTINUATION_TIMEOUT'),
                             ('SIDECAR_START_FAILED', 'SIDECAR_START_FAILED'),
                             ('SIDECAR_NONZERO_EXIT', 'SIDECAR_EXIT_FAILED'),
                             ('PYTHON_RUNTIME_UNAVAILABLE', 'PROVIDER_UNAVAILABLE')):
            coord, snap = self.begin()
            out = self.finish(coord, snap, c.bridge.failure(snap.transport_id, code))
            self.assertEqual(out.reason, reason)
            self.assertEqual(out.host_result, snap.host_result)
            self.assertEqual(coord.request.history[-2][1], 'PROVIDER_CONTINUATION_FAILED')
            self.assertTrue(dict(out.cleanup)['owner_release_required'])

    def test_malformed(self):
        for change in ({'text': ''}, {'text': None}, {'error': {}}, {'protocol_version': True}, {'extra': 1}):
            coord, snap = self.begin()
            out = self.finish(coord, snap, response(snap, **change))
            self.assertEqual(out.reason, 'MALFORMED_CONTINUATION_RESPONSE')
            self.assertEqual(out.host_result, snap.host_result)

    def test_mismatched_ids(self):
        for key in ('request_id', 'call_id', 'previous_response_id', 'model'):
            coord, snap = self.begin()
            self.assertEqual(self.finish(coord, snap, response(snap, **{key: 'other'})).reason, 'RESPONSE_CORRELATION_FAILED')
        coord, snap = self.begin()
        self.assertEqual(self.finish(coord, snap, response(snap, response_id='resp1')).reason, 'RESPONSE_CORRELATION_FAILED')

    def test_second_tool(self):
        coord, snap = self.begin()
        out = self.finish(coord, snap, response(snap, state='TOOL_REQUEST', tool_call={'name': 'anything'}))
        self.assertEqual(out.reason, 'SECOND_TOOL_REQUESTED')
        self.assertTrue(out.second_tool_requested)

    def test_duplicate_across_instances_and_workers(self):
        req, sink, admission = fixture()
        coord = c.Coordinator()
        snap = coord.begin(req, sink, admission, 'fake-model', 20)
        for other in (coord, c.Coordinator()):
            with self.assertRaises(ValueError):
                other.begin(req, sink, admission, 'fake-model', 20)
        self.finish(coord, snap, response(snap))
        with self.assertRaises(ValueError):
            coord.run_worker(snap, lambda *a, **k: self.fail('second process'))
        with self.assertRaises(ValueError):
            coord.finish(snap, response(snap), 22)

    def test_late_and_wrong_snapshot(self):
        coord, snap = self.begin()
        with self.assertRaises(ValueError):
            coord.run_worker(snap._replace(call_id='wrong'))
        coord.run_worker(snap, lambda *a, **k: response(snap))
        coord.close('document_close')
        with self.assertRaises(ValueError):
            coord.finish(snap, response(snap), 22)
        self.assertEqual(coord.request.host_result, snap.host_result)

    def test_no_host_result_or_terminal(self):
        for state in ('WRITE_EXECUTING', 'IDLE', 'COMPLETED', 'CANCELLED', 'EXPIRED'):
            req, sink, adm = fixture()
            with self.assertRaises(ValueError):
                c.Coordinator().begin(req._replace(state=state), sink, adm, 'fake-model', 20)

    def test_handoff_checks(self):
        for field in ('logical_request_id', 'host_request_id', 'document_id', 'session_id', 'owner_type'):
            req, sink, adm = fixture()
            sink.receipt = sink.receipt._replace(**{field: 'wrong'})
            with self.assertRaises(ValueError):
                c.Coordinator().begin(req, sink, adm, 'fake-model', 20)
        for mode in ('undelivered', 'owner_lost', 'closed'):
            req, sink, adm = fixture()
            if mode == 'undelivered': sink.delivered = False
            if mode == 'closed': sink.cleanup()
            if mode == 'owner_lost': adm.release(sink.owner, 'TEST')
            with self.assertRaises(ValueError):
                c.Coordinator().begin(req, sink, adm, 'fake-model', 20)

    def test_optimistic_text_never_overwrites_host(self):
        failed = result('FAILED', 'READ_FAILED')
        indeterminate = result('INDETERMINATE', 'TRANSACTION_PENDING')
        indeterminate.update(transaction_started=True, transaction_status='Pending', model_modified=None)
        verification = result(); verification.update(classification='MEP_PARAMETER_WRITE_FAILED',
                                                       reason_code='VERIFICATION_FAILED', verification_passed=False)
        for data in (failed, indeterminate, verification):
            coord, snap = self.begin(data)
            out = self.finish(coord, snap, response(snap, text='Everything succeeded and was rolled back.'))
            self.assertEqual(p.project_receipt(out.host_result), p.project_receipt(p.freeze_result(data)))
            self.assertEqual(out.provider_status.status, 'COMPLETE')
            if data is indeterminate: self.assertTrue(dict(out.cleanup)['retained_safety_lock'])

    def test_cancel_expiry_intent(self):
        for state, kind, reason, terminal in (('USER_CANCELLED', 'CANCELLED', 'USER_CANCELLED', 'CANCELLED'),
                                             ('APPROVAL_EXPIRED', 'NOT_READY', 'CONFIRMATION_EXPIRED', 'EXPIRED')):
            coord, snap = self.begin(result(kind, reason), PREFIX + CONFIRM[:2] + (state, 'HOST_RESULT_READY'))
            self.finish(coord, snap, response(snap))
            self.assertEqual(coord.request.state, terminal)

    def test_decoder_limits_unicode_and_errors(self):
        _, snap = self.begin()
        decode = lambda raw, exit=0: c.decode_final(raw, snap.transport_id, exit)
        self.assertEqual(decode('x' * 100001)['reason'], 'OUTPUT_TOO_LARGE')
        self.assertEqual(decode('bad')['reason'], 'MALFORMED_CONTINUATION_RESPONSE')
        self.assertEqual(decode('{}', 1)['reason'], 'SIDECAR_EXIT_FAILED')
        self.assertEqual(decode(json.dumps(response(snap, text='x' * 12001)))['reason'], 'OUTPUT_TOO_LARGE')
        self.assertEqual(decode(json.dumps(response(snap, text='\u03bb')))['text'], '\u03bb')
        self.assertEqual(decode('{"request_id":"x","request_id":"x"}')['reason'], 'MALFORMED_CONTINUATION_RESPONSE')

    def test_worker_exception_no_details(self):
        coord, snap = self.begin()
        def raising(*args, **kwargs): raise RuntimeError('fake-private-error')
        out = coord.finish(snap, coord.run_worker(snap, raising), 21)
        self.assertEqual(out.reason, 'INTERNAL_CONTINUATION_ERROR')
        self.assertNotIn('fake-private-error', str(out))


class Sidecar(unittest.TestCase):
    def invoke(self, text='Final', items=None, **fields):
        request, sink, adm = fixture()
        snap = c.prepare(request, sink, adm, 'fake-model', 20)
        config = NS(model='fake-model', api_key='test-fake-secret')
        factory = MagicMock()
        response_data = dict(status='completed', id='resp_final', output_text=text,
                             output=items if items is not None else [NS(type='message')])
        response_data.update(fields)
        factory.return_value.__enter__.return_value.responses.create.return_value = NS(**response_data)
        out = provider.send_write_explanation(config, c.payload(snap), factory)
        return out, factory, snap

    def test_mock_success_no_tools_one_call(self):
        out, factory, snap = self.invoke()
        self.assertEqual(out['state'], 'WRITE_FINAL')
        call = factory.return_value.__enter__.return_value.responses.create
        call.assert_called_once()
        self.assertEqual(call.call_args.kwargs, wire.final_payload(c.payload(snap)))

    def test_second_calls_rejected(self):
        for items in ([NS(type='function_call')], [NS(type='message'), NS(type='function_call')], [NS(type='computer_call')]):
            out, _, _ = self.invoke(items=items)
            self.assertEqual(out['error']['code'], 'AI_TOOL_LOOP_LIMIT')

    def test_empty_oversize_and_secret_redaction(self):
        for text, code in (('', 'OPENAI_EMPTY_RESPONSE'), ('x' * 12001, 'CONTINUATION_OUTPUT_TOO_LARGE'),
                           ('test-fake-secret', 'INTERNAL_PROVIDER_ERROR'), ('Authorization: fake', 'INTERNAL_PROVIDER_ERROR')):
            out, _, _ = self.invoke(text=text)
            self.assertEqual(out['error']['code'], code)
            self.assertIsNone(out['text'])

    def test_bad_final_id(self):
        out, _, _ = self.invoke(id='bad id')
        self.assertFalse(out['ok'])

    def test_existing_provider_functions_source_identical(self):
        import ast, subprocess
        before = ast.parse(subprocess.check_output(['git', 'show', 'HEAD:BIMCode_Provider/provider.py']).decode())
        after = ast.parse((ROOT / 'BIMCode_Provider/provider.py').read_text())
        old = {n.name: ast.dump(n) for n in before.body if isinstance(n, ast.FunctionDef)}
        new = {n.name: ast.dump(n) for n in after.body if isinstance(n, ast.FunctionDef)}
        self.assertTrue(all(new[k] == v for k, v in old.items()))

    def test_mock_sdk_timeout_and_failure(self):
        import openai
        import httpx
        req, sink, adm = fixture()
        snap = c.prepare(req, sink, adm, 'fake-model', 20)
        for exception, expected in ((openai.APITimeoutError(request=httpx.Request('POST', 'https://example.invalid')), 'OPENAI_TIMEOUT'),
                                    (RuntimeError('fake-private-error'), 'INTERNAL_PROVIDER_ERROR')):
            factory = MagicMock()
            factory.return_value.__enter__.return_value.responses.create.side_effect = exception
            out = provider.send_write_explanation(NS(model='fake-model', api_key='fake'), c.payload(snap), factory)
            self.assertEqual(out['error']['code'], expected)
            self.assertNotIn('fake-private-error', str(out))

    def test_dispatch_selects_only_final_sender(self):
        import sidecar
        req, sink, adm = fixture()
        snap = c.prepare(req, sink, adm, 'fake-model', 20)
        with patch.object(sidecar, 'load_config', return_value=NS(state='READY', model='fake-model')), \
                patch.object(provider, 'send') as readonly, patch.object(provider, 'send_write_explanation') as final:
            final.return_value = response(snap)
            self.assertEqual(sidecar.dispatch(json.dumps(c.payload(snap)), ROOT, {}), response(snap))
            final.assert_called_once()
            readonly.assert_not_called()

    def test_extra_host_fields_rejected_at_wire(self):
        req, sink, adm = fixture()
        snap = c.prepare(req, sink, adm, 'fake-model', 20)
        envelope = c.payload(snap)
        data = json.loads(envelope['function_call_output'])
        data['instructions'] = 'execute something'
        envelope['function_call_output'] = json.dumps(data)
        with self.assertRaises(ValueError): wire.final_payload(envelope)
