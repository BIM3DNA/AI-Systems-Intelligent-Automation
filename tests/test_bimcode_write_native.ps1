# Offline IronPython contracts/compile only. Does not launch Revit or provision.
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$pyrevit = Join-Path $env:APPDATA 'pyRevit-Master'
[void][Reflection.Assembly]::LoadFrom((Join-Path $pyrevit 'bin/netfx/engines/IPY2712PR/pyRevitLabs.IronPython.dll'))
$engine = [IronPython.Hosting.Python]::CreateEngine()
$loader = [Reflection.Assembly]::LoadFrom((Join-Path $pyrevit 'bin/netfx/engines/IPY2712PR/pyrevitLoader.dll'))
$archive = Join-Path ([IO.Path]::GetTempPath()) ('m4a-contract-' + [guid]::NewGuid().ToString('N') + '.zip')
$resource = $loader.GetManifestResourceStream('pyRevitLoader.python_2712pr_lib.zip')
$stream = [IO.File]::Create($archive)
try { $resource.CopyTo($stream) } finally { $stream.Dispose(); $resource.Dispose() }
try {
    $paths = $engine.GetSearchPaths()
    $paths.Add($archive)
    $paths.Add((Join-Path $repo 'AI.extension/lib'))
    $engine.SetSearchPaths($paths)
    $scope = $engine.CreateScope()
    $scope.SetVariable('repo', $repo)
    $engine.Execute(@'
import os, sys
sys.dont_write_bytecode = True
from bimcode_ai_pane import write_contracts as c
assert c.M4A_TEST_PARAMETER_GUID == '2f3c955d-45ee-4258-bc61-08acd40a2912'
for value in ('A', u'Pipe 01_A-B', 'A' * 64):
    assert c.validate_value(value)['valid']
for value in ('', ' A', 'A ', ' ', 'A\n', 'A\t', 'A\x00', 'A' * 65, 'A.B', None, 1):
    assert not c.validate_value(value)['valid']
for name in ('AI.extension/lib/bimcode_ai_pane/write_contracts.py',
             'AI.extension/lib/bimcode_write_runtime.py',
             'AI.extension/AI.tab/Dev.panel/M4ASetup.pushbutton/script.py',
             'AI.extension/AI.tab/Dev.panel/M4APreview.pushbutton/script.py',
             'AI.extension/lib/bimcode_write_execution.py',
             'AI.extension/lib/bimcode_ai_pane/write_coordinator.py',
             'AI.extension/AI.tab/Dev.panel/M4AWrite.pushbutton/script.py'):
    with open(os.path.join(repo, name), 'rb') as source:
        compile(source.read(), name, 'exec')
from bimcode_write_execution import freeze
preview = dict(classification=c.PREVIEW_OK, reason_code='COMPLETE', request_id='native')
request = freeze(preview, (1, 2, 3), 1.0, 2.0)
preview['request_id'] = 'changed'
assert 'changed' not in request.preview_json
assert request.epochs == (1, 2, 3)
print('PASS: 17 native contract assertions; 7 IronPython compiles; no Revit execution')
from bimcode_ai_pane.write_access import ControlledWritePermission, document_eligibility
from bimcode_ai_pane.controlled_write_registry import metadata, validate_arguments
facts = dict(valid_document=True, active_uidocument=True, family_document=False,
             host_document=True, linked_document=False, workshared=False,
             read_only=False, modifiable=False, fixed_parameter_available=True,
             fixed_parameter_binding_valid=True)
permission = ControlledWritePermission()
assert not permission.view_model()['enabled']
assert document_eligibility(facts)['eligible']
assert permission.enable_from_human('doc', facts, True)
assert not permission.view_model()['provider_exposure_allowed']
permission.document_closed()
assert not permission.view_model()['enabled']
assert len(metadata()) == 1
assert metadata()[0]['dispatcher_state'] == 'NOT_IMPLEMENTED'
assert validate_arguments({'value': u'M4A_AI_01'})['valid']
assert not validate_arguments({'value': 'A', 'confirmed': True})['valid']
assert not validate_arguments({'value': 'A\n'})['valid']
for name in ('write_access.py', 'controlled_write_registry.py'):
    with open(os.path.join(repo, 'AI.extension/lib/bimcode_ai_pane', name), 'rb') as source:
        compile(source.read(), name, 'exec')
print('PASS: 10 M4B native assertions; 2 additional IronPython compiles')
from bimcode_ai_pane import write_projection as projection
from bimcode_ai_pane import provider_write as machine
assert len(machine.STATES) == 22
identity = machine.correlation('logical1', 'host1', 'session1', 'doc1', 'resp1', 'call1', 'New')
request = machine.new_request(identity, 0)
assert request.state == 'IDLE'
assert not machine.transition(request, identity, 'WRITE_EXECUTING', 1, 'TEST').accepted
assert machine.transition(request, identity, 'PROVIDER_INITIAL_REQUEST', 1, 'TEST').accepted
assert projection.explanation('FAILED').status == 'FAILED'
from bimcode_write_execution import result_for
receipt = projection.from_host_result(result_for(dict(request_id='host1'), 'CANCELLED', 'USER_CANCELLED'))
assert projection.project_receipt(receipt)['model_modified'] is False
assert projection.provenance(receipt)['transaction'] == 'NOT_STARTED'
for name in ('write_projection.py', 'provider_write.py'):
    with open(os.path.join(repo, 'AI.extension/lib/bimcode_ai_pane', name), 'rb') as source:
        compile(source.read(), name, 'exec')
print('PASS: 7 M4B coordination assertions; 2 additional IronPython compiles')
from bimcode_ai_pane.write_access import OperationAdmission
from bimcode_ai_pane.write_completion import CompletionSink
admission = OperationAdmission()
owner = admission.acquire('HUMAN_DEV_WRITE', 'host1', 'host1', 'doc1', 'session1', 1)
assert owner is not None
assert admission.acquire('PARAMETER_PROVISIONING', 'host2', 'host2', 'doc1', 'session1', 2) is None
sink = CompletionSink(owner)
assert sink.store(result_for(dict(request_id='host1'), 'CANCELLED', 'USER_CANCELLED'))
assert sink.deliver('host1')
assert not sink.deliver('host1')
assert admission.cleanup(owner, 'DOCUMENT_CLOSE', transaction_unresolved=True)
assert admission.safety_locked
with open(os.path.join(repo, 'AI.extension/lib/bimcode_ai_pane/write_completion.py'), 'rb') as source:
    compile(source.read(), 'write_completion.py', 'exec')
print('PASS: 7 M4B admission/callback assertions; 1 additional IronPython compile')
from bimcode_ai_pane.write_clock import Clock
from bimcode_ai_pane import write_leases as leases_module
from bimcode_ai_pane.write_lifecycle import Lifecycle
from bimcode_ai_pane.write_access import ControlledWritePermission
native_clock = Clock()
assert native_clock.sample().monotonic <= native_clock.sample().monotonic
now = [1000.0]
clock = Clock(lambda: now[0], lambda: '2026-10-01T12:00:00Z')
admission = OperationAdmission()
owner = admission.acquire('CONTROLLED_WRITE_PROVIDER_TOOL', 'logical1', 'host1', 'doc1', 'session1', 0)
bound = leases_module.binding(identity, owner, 'fingerprint', 123, 'unique1', False, None, 1, 2)
leases = leases_module.Leases(clock)
assert leases.preview.state == 'NOT_STARTED'
assert leases.create_preview(bound).accepted
assert leases.preview.expires_at == 1120
now[0] = 1119.999
assert leases.check('PREVIEW', bound).accepted
assert leases.confirm(bound, True).accepted
assert leases.preview.consumed
assert leases.queue.created_at == now[0]
assert leases.queue.expires_at == now[0] + 30
assert not leases.confirm(bound, True).accepted
now[0] = leases.queue.expires_at
assert leases.handler_started(bound).reason == 'EXECUTION_QUEUE_LEASE_EXPIRED'
assert not leases.queue.consumed
assert not leases.handler_started(bound).accepted
request = machine.new_request(identity, 0)
for index, state in enumerate(('PROVIDER_INITIAL_REQUEST', 'PROVIDER_TOOL_SELECTED', 'WRITE_ARGUMENTS_VALIDATED',
                             'HOST_PREVIEW_BUILDING', 'PREVIEW_READY', 'AWAITING_HUMAN_CONFIRMATION', 'WRITE_REQUEST_QUEUED')):
    request = machine.transition(request, identity, state, index + 1, 'TEST').request
ready = leases_module.expired_request(request, leases)
host = projection.project_receipt(ready.host_result)
assert ready.state == 'HOST_RESULT_READY'
assert ready.terminal_intent == 'EXPIRED'
assert host['reason_code'] == 'EXECUTION_QUEUE_LEASE_EXPIRED'
assert host['transaction_started'] is False
assert host['model_modified'] is False
sink = CompletionSink(owner)
sink.store(host)
permission = ControlledWritePermission()
lifecycle = Lifecycle(owner, admission, permission, leases, sink)
cleaned = lifecycle.document_close(ready)
assert cleaned.owner_released
assert cleaned.host_result == ready.host_result
assert sink.closed
assert lifecycle.document_close(ready) is cleaned
assert admission.active is None
for name in ('write_clock.py', 'write_leases.py', 'write_lifecycle.py', 'provider_write.py'):
    with open(os.path.join(repo, 'AI.extension/lib/bimcode_ai_pane', name), 'rb') as source:
        compile(source.read(), name, 'exec')
print('PASS: 23 M4B lease/lifecycle assertions; 3 additional IronPython compiles; reducer recompiled')
from bimcode_ai_pane.session_write_gate import SessionWriteGate
gate = SessionWriteGate(OperationAdmission())
assert gate.view_model()['status'] == 'CONTROLLED WRITES: DISABLED'
gate.observe('doc', facts)
assert gate.queue_enable()
ticket, gate.enable_pending = gate.enable_pending, None
assert not gate.enable(ticket, False)
assert gate.enable(ticket, True)
assert gate.view_model()['status'] == 'CONTROLLED WRITES: ENABLED FOR THIS SESSION'
assert gate.view_model()['active_provider_tool_count'] == 13
assert gate.view_model()['controlled_write_metadata_count'] == 1
assert not gate.view_model()['controlled_write_provider_exposed']
assert not gate.view_model()['controlled_write_dispatch_available']
assert gate.view_model()['eligibility_text'] == 'Eligible: YES (COMPLETE)'
gate.cleanup('DOCUMENT_CLOSE')
assert not gate.view_model()['controlled_write_permission_enabled']
assert gate.view_model()['eligibility_text'] == 'Eligible: NO (NO_VALID_DOCUMENT)'
generation = gate.cleanup_generation
gate.cleanup('DOCUMENT_CLOSE')
assert gate.cleanup_generation == generation
assert not SessionWriteGate(OperationAdmission()).permission.view_model()['enabled']
for name in ('session_write_gate.py', 'lifecycle.py', 'panel.py'):
    with open(os.path.join(repo, 'AI.extension/lib/bimcode_ai_pane', name), 'rb') as source:
        compile(source.read(), name, 'exec')
print('PASS: 14 M4B-8A gate assertions; 3 additional IronPython compiles')
'@, $scope) | Out-Null
} finally {
    Remove-Item -LiteralPath $archive
}
