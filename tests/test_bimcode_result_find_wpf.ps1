# Native WPF/IronPython smoke test. No Revit process, model, or network access.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework
$repo = Split-Path $PSScriptRoot -Parent
$pane = Join-Path $repo 'AI.extension/lib/bimcode_ai_pane'
$pyrevit = Join-Path $env:APPDATA 'pyRevit-Master'
[void][Reflection.Assembly]::LoadFrom((Join-Path $pyrevit 'bin/netfx/engines/IPY2712PR/pyRevitLabs.IronPython.dll'))
$engine = [IronPython.Hosting.Python]::CreateEngine()
foreach ($assembly in @([System.Windows.Documents.FlowDocument].Assembly, [System.Windows.Media.FontFamily].Assembly, [System.Windows.Thickness].Assembly)) {
    $engine.Runtime.LoadAssembly($assembly)
}
$paths = $engine.GetSearchPaths()
$paths.Add((Join-Path $pyrevit 'pyrevitlib'))
$paths.Add((Join-Path $pyrevit 'site-packages'))
$engine.SetSearchPaths($paths)
$scope = $engine.CreateScope()
$scope.SetVariable('find_source', (Get-Content -Raw (Join-Path $pane 'result_find.py')))
$engine.Execute(@'
import sys
package = type(sys)('bimcode_ai_pane')
package.__path__ = []
sys.modules['bimcode_ai_pane'] = package
module = type(sys)('bimcode_ai_pane.result_find')
exec(find_source, module.__dict__)
sys.modules['bimcode_ai_pane.result_find'] = module
'@, $scope)
$engine.Execute((Get-Content -Raw (Join-Path $pane 'rich_result.py')), $scope)
$engine.Execute((Get-Content -Raw (Join-Path $pane 'theme.py')), $scope)
$reader = [System.Xml.XmlReader]::Create((Join-Path $pane 'BIMCodeAIPane.xaml'))
try { $page = [System.Windows.Markup.XamlReader]::Load($reader) } finally { $reader.Close() }
$scope.SetVariable('page', $page)
$engine.Execute(@'
from System.Windows.Documents import TextRange
from System.Diagnostics import Stopwatch
model = {'blocks': [dict(kind='fact', label='System: ', text='Hydronic Supply', tone='PrimaryTextBrush'),
                    dict(kind='heading', label='', text='Details', tone='PrimaryTextBrush'),
                    dict(kind='technical', label='Name: ', text='a' * 15954, tone='PrimaryTextBrush')]}
finder = module.ResultFind()
finder.search(model, 'a')
watch = Stopwatch.StartNew()
document = make_document(model, finder)
watch.Stop()
print('Dense-match document construction: {0} matches, {1} ms'.format(len(finder.matches), watch.ElapsedMilliseconds))
page.FindName('ToolResultText').Document = document
expected = ''.join(b['label'] + b['text'] + '\r\n' for b in model['blocks'])
assert len(expected) <= 16000
assert TextRange(document.ContentStart, document.ContentEnd).Text == expected
for name in ('light', 'dark'):
    apply_resources(page.Resources, name)
    assert document.Tag.Background.Color == page.Resources['AccentBrush'].Color
    assert document.Tag.Foreground.Color == page.Resources['SurfaceBrush'].Color
finder.move(-1)
document = make_document(model, finder)
page.FindName('ToolResultText').Document = document
assert TextRange(document.ContentStart, document.ContentEnd).Text == expected
assert document.Tag is not None
finder.search(model, '')
assert finder.caption() == '0/0'
plain = make_document(model)
assert TextRange(plain.ContentStart, plain.ContentEnd).Text == expected
'@, $scope)
$page.Measure([System.Windows.Size]::new(260,650))
$page.Arrange([System.Windows.Rect]::new(0,0,260,650))
$page.UpdateLayout()
$scope.GetVariable('document').Tag.BringIntoView()
foreach ($filename in @('panel.py', 'rich_result.py', 'result_find.py', 'result_presentation.py')) {
    [void]$engine.CreateScriptSourceFromFile((Join-Path $pane $filename)).Compile()
}
'PASS: native XAML, dense highlights, exact text/bound, theme resources, active-match scrolling, IronPython compile'
