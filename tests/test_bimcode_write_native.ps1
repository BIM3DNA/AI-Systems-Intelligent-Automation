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
'@, $scope) | Out-Null
} finally {
    Remove-Item -LiteralPath $archive
}
