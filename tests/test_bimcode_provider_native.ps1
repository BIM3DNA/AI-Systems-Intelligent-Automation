# Native IronPython process/dispatcher tests. Only fake child; no real config/API.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName WindowsBase
$repo = Split-Path $PSScriptRoot -Parent
$pyrevit = Join-Path $env:APPDATA 'pyRevit-Master'
[void][Reflection.Assembly]::LoadFrom((Join-Path $pyrevit 'bin/netfx/engines/IPY2712PR/pyRevitLabs.IronPython.dll'))
$engine = [IronPython.Hosting.Python]::CreateEngine()
$loader = [Reflection.Assembly]::LoadFrom((Join-Path $pyrevit 'bin/netfx/engines/IPY2712PR/pyrevitLoader.dll'))
$stdlibZip = Join-Path ([IO.Path]::GetTempPath()) ('bimcode-ipy-' + [guid]::NewGuid().ToString('N') + '.zip')
$resource = $loader.GetManifestResourceStream('pyRevitLoader.python_2712pr_lib.zip')
$zipFile = [IO.File]::Create($stdlibZip)
try { $resource.CopyTo($zipFile) } finally { $zipFile.Dispose(); $resource.Dispose() }
$paths = $engine.GetSearchPaths()
$paths.Add($stdlibZip)
$paths.Add((Join-Path $pyrevit 'pyrevitlib'))
$paths.Add((Join-Path $pyrevit 'site-packages'))
$paths.Add((Join-Path $repo 'AI.extension/lib'))
$engine.SetSearchPaths($paths)
$engine.Runtime.LoadAssembly([System.Windows.Threading.Dispatcher].Assembly)
$scope = $engine.CreateScope()
$scope.SetVariable('repo', $repo)
$engine.Execute(@'
import os
import sys
sys.dont_write_bytecode = True
from bimcode_ai_pane import provider_bridge as bridge
from bimcode_ai_pane import provider_ui
from System import Action
from System.Threading import Thread
from System.Windows.Threading import Dispatcher, DispatcherFrame

executable, script, root = bridge.paths()
assert root == repo
fake = os.path.join(repo, 'tests', 'fixtures', 'provider_fake.py')
bridge.paths = lambda: (executable, fake, root)
checks = 0
def check(mode, code=None):
    global checks
    result = bridge.run(bridge.request('text_response', mode))
    assert result['error']['code'] == code if code else result['ok'], str(result)
    assert 'fake-private-error' not in str(result)
    checks += 1
check('valid')
check('stderr')
check('malformed', 'SIDECAR_PROTOCOL_ERROR')
check('mismatch', 'SIDECAR_REQUEST_ID_MISMATCH')
check('nonzero', 'SIDECAR_NONZERO_EXIT')
bridge.TIMEOUT_MS = 100
check('timeout', 'SIDECAR_TIMEOUT')
bridge.TIMEOUT_MS = 75000
bridge.paths = lambda: (executable + '.missing', fake, root)
check('valid', 'PYTHON_RUNTIME_UNAVAILABLE')
bridge.paths = lambda: (executable, fake + '.missing', root)
check('valid', 'SIDECAR_START_FAILED')
bridge.paths = lambda: (fake, fake, root)
check('valid', 'SIDECAR_START_FAILED')
bridge.paths = lambda: (executable, fake, root)

# Real .NET worker -> WPF dispatcher; no controls touched on worker.
dispatcher = Dispatcher.CurrentDispatcher
owner = Thread.CurrentThread.ManagedThreadId
frame = DispatcherFrame()
completed = []
def complete(result):
    assert Thread.CurrentThread.ManagedThreadId == owner
    completed.append(result)
    frame.Continue = False
provider_ui.launch(bridge.request('text_response', 'valid'), dispatcher, complete)
Dispatcher.PushFrame(frame)
assert len(completed) == 1 and completed[0]['ok']
checks += 1
print('PASS {0} native process/dispatcher probes'.format(checks))
'@, $scope)
foreach ($filename in @('panel.py', 'provider_bridge.py', 'provider_ui.py', 'ai_tool.py', 'lifecycle.py')) {
    [void]$engine.CreateScriptSourceFromFile((Join-Path $repo ('AI.extension/lib/bimcode_ai_pane/' + $filename))).Compile()
}
'PASS IronPython compilation of 5 M3A/M3B Revit-side files'
$engine.Execute(@'
import json
from bimcode_ai_pane import ai_tool
class Scalar(object):
    pass
session = Scalar()
session.document_identity = (1, 'doc', 'path')
session.context_generation = 1
session.selection_generation = 1
session.tools = Scalar()
session.tools.pending = None
session.raise_ai_event = lambda: True
uidoc = Scalar()
uidoc.Document = object()
app = Scalar()
app.ActiveUIDocument = uidoc
ai_tool.document_key = lambda app: session.document_identity
ai_tool.resolve_headless_modelmind_specialty = lambda d, u: dict(ok=True, specialties=['PIPING'])
executions = []
def execute(action, d, u):
    executions.append(action)
    return dict(ok=True, action_id=ai_tool.ACTION, specialty='PIPING',
                classification='PIPING_SELECTION_SUMMARY_OK', reason_code='COMPLETE', summary=['Count: 1'])
ai_tool.execute_headless_modelmind_readonly = execute
rid = 'a' * 32
response = dict(protocol_version=1, request_id=rid, ok=True, provider='openai', model='test-model',
                text=None, error=None, state='TOOL_REQUEST',
                tool_call=dict(call_id='call_1', name=ai_tool.NAME, arguments={}),
                provider_state=dict(response_id='resp_1', model='test-model'))
coordinator = ai_tool.Coordinator(session)
completed = []
def done(error, data):
    completed.append((error, data))
assert coordinator.begin(rid)
coordinator.queue(response, done)
assert not executions
coordinator.execute_approved(app)
assert executions == [ai_tool.ACTION] and completed[-1][1]['summary'] == ['Count: 1']
coordinator.queue(response, done)
assert completed[-1][0]['error']['code'] == 'AI_TOOL_LOOP_LIMIT'
coordinator.clear()
assert coordinator.begin(rid)
session.selection_generation += 1
coordinator.queue(response, done)
coordinator.execute_approved(app)
assert completed[-1][0]['error']['code'] == 'STALE_CONTEXT'
assert len(executions) == 1
assert bridge.decode(json.dumps(response), rid, 0)['state'] == 'TOOL_REQUEST'
print('PASS 4 native M3B probes: one-action parity, loop limit, stale selection, tool envelope')
'@, $scope)
