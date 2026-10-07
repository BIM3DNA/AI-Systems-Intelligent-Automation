# Real TWO-engine ownership regression. Fake Revit API only; no Revit/network.
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$pyrevitRoot = Join-Path $env:APPDATA 'pyRevit-Master'
[void][Reflection.Assembly]::LoadFrom((Join-Path $pyrevitRoot 'bin/netfx/engines/IPY2712PR/pyRevitLabs.IronPython.dll'))
$loader = [Reflection.Assembly]::LoadFrom((Join-Path $pyrevitRoot 'bin/netfx/engines/IPY2712PR/pyrevitLoader.dll'))
$archive = Join-Path ([IO.Path]::GetTempPath()) ('m4b-engine-' + [guid]::NewGuid().ToString('N') + '.zip')
$resource = $loader.GetManifestResourceStream('pyRevitLoader.python_2712pr_lib.zip')
$stream = [IO.File]::Create($archive)
try { $resource.CopyTo($stream) } finally { $stream.Dispose(); $resource.Dispose() }
try {
    $a = [IronPython.Hosting.Python]::CreateEngine()
    $b = [IronPython.Hosting.Python]::CreateEngine()
    foreach ($engine in @($a,$b)) {
        $paths=$engine.GetSearchPaths(); $paths.Add($archive); $paths.Add((Join-Path $repo 'AI.extension/lib'))
        $engine.SetSearchPaths($paths)
    }
    $sa=$a.CreateScope(); $sb=$b.CreateScope(); $sa.SetVariable('repo',$repo)
    $a.Execute(@'
import sys, os, json, types
sys.dont_write_bytecode=True
from bimcode_ai_pane import write_contracts as c
class N(object):
    def __init__(self, **kwargs): self.__dict__.update(kwargs)
# Reuse real preview fake-DB fixture, without importing CPython-only test tools.
source=open(os.path.join(repo,'tests/test_bimcode_write_runtime.py')).read()
exec(source[source.index('class Identity:'):source.index('class Preview(')])
f=fixture()
f.doc.PathName=''; f.doc.IsLinked=False; f.db.ElementId=Identity
def forbidden(*args): raise AssertionError('Mutation forbidden in Cancel probe')
f.db.Transaction=forbidden; f.parameter.Set=forbidden
from bimcode_ai_pane.write_access import admission_for, Owner
from bimcode_ai_pane.session_write_gate import SessionWriteGate, read_document
from bimcode_ai_pane.provider_write_session import SessionWrites
from bimcode_ai_pane.provider_write_dispatch import Dispatcher
from bimcode_ai_pane import provider_write_confirmation as confirmation
s=N(uiapp=f.app, document_identity=(123,'Fixture',''),context_generation=0,
    selection_generation=1,m4a_write=N(epoch=0),tools=N(pending=None),ai=N(turn=None))
s.write_gate=SessionWriteGate(admission_for(s))
document,facts=read_document(f.app,f.db,f.guid)
s.write_gate.observe(document,facts)
def enable(): s.write_gate.permission.enable_from_human(document,facts,True)
enable()
# Replace only unavailable Revit import/event/dialog edges, in engine A.
Dispatcher.dispatch=lambda self,uiapp,call,response:self._dispatch(uiapp,call,response,f.db,f.guid)
from bimcode_ai_pane.provider_write_host_bridge import Bridge
Bridge._api=lambda self:(f.db,f.guid)
fake_ui=N(IExternalEventHandler=object,ExternalEvent=N(Create=lambda h:N(Raise=lambda:'Accepted')),
          ExternalEventRequest=N(Accepted='Accepted'))
sys.modules['Autodesk']=types.ModuleType('Autodesk')
sys.modules['Autodesk.Revit']=N(UI=fake_ui)
sys.modules['bimcode_ai_pane.write_coordinator']=N(get_coordinator=lambda session:session.m4a_write)
dialog_states=[]
def cancel(preview,identity):
    dialog_states.append(s.controlled_writes.dispatcher.request.state)
    return False
confirmation.show=cancel
s.controlled_writes=SessionWrites(s)
s.begin_controlled_write_request=s.controlled_writes.begin
s.confirm_controlled_write_request=s.controlled_writes.confirm
s.inspect_controlled_write_request=s.controlled_writes.inspect
'@,$sa)
    $sb.SetVariable('session',$sa.GetVariable('s'))
    $b.Execute(@'
import sys,json
sys.dont_write_bytecode=True
count=0
def check(condition):
    global count
    assert condition
    count+=1
result=json.loads(session.begin_controlled_write_request(u'M4B_HOST_CANCEL_02'))
check(result['accepted'])
request_id=result['host_request_id']
snapshot=json.loads(session.inspect_controlled_write_request())
check(snapshot['state']=='AWAITING_HUMAN_CONFIRMATION')
check(snapshot['leases']['preview']['state']=='ACTIVE')
check(snapshot['leases']['preview']['binding'] is not None)
check(snapshot['preview']['classification']=='MEP_PARAMETER_WRITE_PREVIEW_OK')
# Original topology still rejects: do not weaken strict class checks.
from bimcode_ai_pane.write_access import Owner
from bimcode_ai_pane.provider_write import correlation
from bimcode_ai_pane.write_leases import binding
foreign=session.write_admission.active
check(type(foreign) is not Owner)
i=correlation(foreign.logical_request_id,foreign.host_request_id,foreign.session_id,foreign.document_id,value='M4B_HOST_CANCEL_02')
try:
    binding(i,foreign,'a'*64,1,'pipe-1',False,None,0,0)
except ValueError as e:
    check(str(e)=='LEASE_CORRELATION_FAILED')
else: raise AssertionError('Original defect topology unexpectedly accepted')
# All authority/correlation injection is excluded from the scalar API signature.
for field in ('owner','token','owner_kind','logical_request_id','call_id','previous_response_id',
              'document_id','session_id','target','guid','action','clock','binding','state'):
    try: session.begin_controlled_write_request('Value',**{field:'forged'})
    except TypeError: check(True)
    else: raise AssertionError(field)
check(json.loads(session.confirm_controlled_write_request('wrong-host'))['reason']=='CORRELATION_MISMATCH')
for field in ('value','call_id','response_id','confirmed','owner','token'):
    try: session.confirm_controlled_write_request(request_id,**{field:'forged'})
    except TypeError: check(True)
    else: raise AssertionError(field)
check(json.loads(session.begin_controlled_write_request('Competing'))['reason']=='EXECUTION_BUSY')
cancelled=json.loads(session.confirm_controlled_write_request(request_id))
check(cancelled['state']=='CANCELLED')
check(cancelled['host_result']['reason_code']=='USER_CANCELLED')
check(cancelled['host_result']['model_modified'] is False)
check(cancelled['host_result']['transaction_started'] is False)
check(session.write_admission.active is None)
check(not json.loads(session.confirm_controlled_write_request(request_id))['accepted'])
'@,$sb)
    $a.Execute(@'
assert dialog_states==['AWAITING_HUMAN_CONFIRMATION']
assert type(s.controlled_writes.dispatcher.owner) is Owner
from bimcode_ai_pane.provider_write import Request, Correlation
from bimcode_ai_pane.write_leases import Binding, Lease
from bimcode_ai_pane.write_clock import Clock
from bimcode_ai_pane.write_completion import Completion
from bimcode_ai_pane.write_projection import Receipt
assert type(s.controlled_writes.dispatcher.request) is Request
assert type(s.controlled_writes.dispatcher.identity) is Correlation
assert type(s.controlled_writes.dispatcher.context_binding) is Binding
assert type(s.controlled_writes.dispatcher.leases.preview) is Lease
assert type(s.controlled_writes.dispatcher.clock) is Clock
assert type(s.controlled_writes.dispatcher.sink.receipt) is Completion
assert type(s.controlled_writes.dispatcher.request.host_result) is Receipt
retained=s.controlled_writes.dispatcher
enable()
'@,$sa)
    # A new scope in caller engine B represents the next Dev invocation.
    $sb2=$b.CreateScope(); $sb2.SetVariable('session',$sa.GetVariable('s'))
    $b.Execute(@'
import json
old=json.loads(session.inspect_controlled_write_request())
assert old['state']=='CANCELLED'
fresh=json.loads(session.begin_controlled_write_request('Fresh'))
assert fresh['accepted'] and fresh['host_request_id']!=old['correlation']['host_request_id']
assert json.loads(session.confirm_controlled_write_request(old['correlation']['host_request_id']))['reason']=='CORRELATION_MISMATCH'
request_id=fresh['host_request_id']
'@,$sb2)
    $a.Execute(@'
assert s.controlled_writes.dispatcher is not retained
assert retained.request.state=='CANCELLED'
assert s.provider_write_bridge is not None
s.write_gate.cleanup('PANE_DISPOSAL')
'@,$sa)
    $b.Execute(@'
invalid=json.loads(session.confirm_controlled_write_request(request_id))
assert invalid['host_result']['reason_code']=='PREVIEW_LEASE_INVALIDATED'
assert invalid['host_result']['model_modified'] is False
assert json.loads(session.begin_controlled_write_request('Revive'))['reason']=='PERMISSION_DISABLED'
assert json.loads(session.inspect_controlled_write_request())==invalid
'@,$sb2)
    $checks=$sb.GetVariable('count')
    Write-Output "PASS: two installed IronPython engines; $checks counted boundary assertions; 19 additional identity/repeated-invocation/lifecycle assertions; original failure reproduced; corrected Cancel passed"
} finally { [IO.File]::Delete($archive) }
