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
'@, $scope) | Out-Null
} finally {
    Remove-Item -LiteralPath $archive
}
