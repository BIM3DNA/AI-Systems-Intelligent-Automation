# Persistent engine plus separate Dev engines. Fake Revit API; no Revit/network.
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
    $sa.SetVariable('pyrevitRoot',$pyrevitRoot)
    $legacySource = (& git -C $repo show '000c9ec13f87be805fcaa64a5bdaeed9bc865518:AI.extension/lib/bimcode_ai_pane/lifecycle.py') -join "`n"
    if ($LASTEXITCODE -ne 0) { throw 'Cannot load the pre-session-API regression baseline' }
    $sa.SetVariable('legacy_source',$legacySource)
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
from bimcode_ai_pane.provider_write_dispatch import Dispatcher
from bimcode_ai_pane import provider_write_confirmation as confirmation
# Import/construct the REAL PaneSession, not a stand-in with manually attached
# SessionWrites methods. Only unavailable Revit/presentation edges are fake.
import imp
from System import AppDomain
class Event(object):
    def __init__(self): self.handlers=[]
    def __iadd__(self, callback): self.handlers.append(callback); return self
    def __isub__(self, callback): self.handlers.remove(callback); return self
class Delegates(object):
    def __getitem__(self, event_type): return lambda callback:callback
class Panel(object):
    def bind_write_gate(self,*args): pass
    def bind_ai(self,*args): pass
    def bind_refresh(self,*args): pass
    def bind_tools(self,*args): pass
    def render(self,*args): pass
    def render_write_gate(self,*args): pass
registered=[]
ui=N(IDockablePaneProvider=object,IExternalEventHandler=object,
     DockablePaneId=lambda value:value,DockablePane=N(PaneIsRegistered=lambda value:bool(registered)),
     ExternalEvent=N(Create=lambda handler:N(Raise=lambda:'Accepted',Dispose=lambda:None)),
     ExternalEventRequest=N(Accepted='Accepted',Pending='Pending'),
     Events=N(ViewActivatedEventArgs=object))
pyrevit=types.ModuleType('pyrevit')
pyrevit.UI=ui; pyrevit.DB=f.db
f.db.Events=N(DocumentOpenedEventArgs=object,DocumentCreatedEventArgs=object,DocumentClosedEventArgs=object)
framework=types.ModuleType('pyrevit.framework')
framework.AppDomain=AppDomain; framework.Guid=N(Parse=lambda value:f.guid)
framework.EventHandler=Delegates()
pyrevit.framework=framework; pyrevit.forms=N(WPFPanel=object)
sys.modules['pyrevit']=pyrevit; sys.modules['pyrevit.framework']=framework
sys.modules['pyrevit.labs']=N(Common=N(PyRevitLabsConsts=N(ProductName='pyRevit')))
# Use installed pyRevit's exact AppDomain persistence implementation. This
# isolated PowerShell process has no connection to the running Revit session.
envvars=imp.load_source('probe_envvars',os.path.join(pyrevitRoot,'pyrevitlib/pyrevit/coreutils/envvars.py'))
sys.modules['pyrevit.coreutils']=N(envvars=envvars)
sys.modules['bimcode_ai_pane.panel']=N(BIMCodeAIPanel=Panel)
f.app.Application=N(DocumentOpened=Event(),DocumentCreated=Event(),DocumentClosed=Event())
f.app.ViewActivated=Event()
f.app.RegisterDockablePane=lambda *args:registered.append(args)
f.app.GetDockablePane=lambda *args:N(Show=lambda:None)
from bimcode_ai_pane import lifecycle
from bimcode_ai_pane import SESSION_KEY
s=lifecycle.start(f.app)
assert type(s) is lifecycle.PaneSession
assert lifecycle.start(f.app) is s and len(registered)==1
assert envvars.get_pyrevit_env_var(SESSION_KEY) is s
assert len(s._subscriptions)==4
assert all(name not in s.__dict__ for name in ('begin_controlled_write_request',
    'confirm_controlled_write_request','inspect_controlled_write_request'))
# Demonstrate the stale-class alternative without claiming it occurred live.
# Reload/start preserves an existing registered session; it does not retrofit
# a pre-002A instance with a newly imported class's methods.
legacy=types.ModuleType('probe_legacy_lifecycle')
exec(compile(legacy_source,'pre_002A_lifecycle.py','exec'),legacy.__dict__)
old_session=legacy.PaneSession(f.app)
assert not hasattr(old_session,'inspect_controlled_write_request')
envvars.set_pyrevit_env_var(SESSION_KEY,old_session)
assert lifecycle.start(f.app) is old_session
assert not hasattr(envvars.get_pyrevit_env_var(SESSION_KEY),'inspect_controlled_write_request')
assert old_session.write_admission.active is None
envvars.set_pyrevit_env_var(SESSION_KEY,s)
s.m4a_write=N(epoch=0)
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
'@,$sa)
    $sb.SetVariable('pyrevitRoot',$pyrevitRoot)
    $b.Execute(@'
import sys,json,types,imp,os
from System import AppDomain
sys.dont_write_bytecode=True
framework=types.ModuleType('pyrevit.framework'); framework.AppDomain=AppDomain
sys.modules['pyrevit']=types.ModuleType('pyrevit')
sys.modules['pyrevit.framework']=framework
labs=types.ModuleType('pyrevit.labs')
class N(object):
    def __init__(self,**kwargs): self.__dict__.update(kwargs)
labs.Common=N(PyRevitLabsConsts=N(ProductName='pyRevit'))
sys.modules['pyrevit.labs']=labs
envvars=imp.load_source('probe_envvars',os.path.join(pyrevitRoot,'pyrevitlib/pyrevit/coreutils/envvars.py'))
from bimcode_ai_pane import SESSION_KEY
session=envvars.get_pyrevit_env_var(SESSION_KEY)
count=0
def check(condition):
    global count
    assert condition
    count+=1
for name,argc in (('begin_controlled_write_request',2),
                  ('confirm_controlled_write_request',2),('inspect_controlled_write_request',1)):
    method=getattr(session,name)
    check(callable(method))
    check(method.im_func.func_code.co_argcount==argc)
    check(method.im_self is session)
check(isinstance(session.inspect_controlled_write_request(),basestring))
check(json.loads(session.inspect_controlled_write_request())['reason']=='NO_RETAINED_HARNESS_REQUEST')
check(session.write_admission.active is None)
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
assert s.write_gate.permission.view_model()['enabled']  # No re-enable after Cancel.
'@,$sa)
    # A fresh engine, not just a new scope: retrieve the SAME persisted object.
    $c=[IronPython.Hosting.Python]::CreateEngine(); $c.SetSearchPaths($b.GetSearchPaths())
    $sb2=$c.CreateScope(); $sb2.SetVariable('envvars',$sb.GetVariable('envvars'))
    $sb2.SetVariable('session_key',$sa.GetVariable('SESSION_KEY'))
    $c.Execute(@'
import sys,json
sys.dont_write_bytecode=True
session=envvars.get_pyrevit_env_var(session_key)
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
    $c.Execute(@'
invalid=json.loads(session.confirm_controlled_write_request(request_id))
assert invalid['host_result']['reason_code']=='PREVIEW_LEASE_INVALIDATED'
assert invalid['host_result']['model_modified'] is False
assert json.loads(session.begin_controlled_write_request('Revive'))['reason']=='PERMISSION_DISABLED'
assert json.loads(session.inspect_controlled_write_request())==invalid
'@,$sb2)
    $a.Execute(@'
# 003A recorded-shape internal adapter; no production routing or network.
from bimcode_ai_pane.write_clock import Clock
from bimcode_ai_pane import provider_write_handoff as handoff_module
from bimcode_ai_pane import write_continuation
write_continuation.Coordinator.run_worker=forbidden
document,facts=read_document(f.app,f.db,f.guid)
s.write_gate.observe(document,facts)
s.write_gate.permission.enable_from_human(document,facts,True)
s.panel._provider_state=N(active=dict(request_id='native_transport',operation='agent_turn'))
s.ai.turn=dict(request_id='native_transport',key=s.document_identity,
              generation=s.context_generation,selection=s.selection_generation,used=False)
h=s.controlled_writes.handoff
ticket=h.open_transport(s.panel._provider_state.active,'fixture-model')
binding=h.bind_response(ticket,dict(protocol_version=1,request_id='native_transport',ok=True,
    provider='openai',model='fixture-model',text=None,error=None,state='TOOL_REQUEST',
    tool_call=dict(name='set_selected_pipe_test_text',call_id='native_call',arguments=dict(value='Native')),
    provider_state=dict(response_id='native_response',model='fixture-model')))
assert type(binding) is handoff_module.Binding
# Offline fixture relinquishes the read-only turn; production transfer is NOT wired.
s.ai.turn=None
hold_now=[10.0]
d=Dispatcher(s,binding.identity,Clock(lambda:hold_now[0],lambda:'fixture-time'),True)
s.controlled_writes.dispatcher=d
out=d._dispatch(f.app,dict(name=binding.identity.tool_name,call_id='native_call',arguments=dict(value='Native')),
                'native_response',f.db,f.guid)
assert out.accepted
s.confirm_controlled_write_request(binding.identity.host_request_id)
assert d.request.state=='PROVIDER_CONTINUATION_PENDING'
assert d.sink.delivered and d.sink.closed and d.sink.continuation_claimed
assert s.write_admission.active is None
assert not h.pending[1]._worker_started
'@,$sa)
    $c.Execute(@'
pending=json.loads(session.inspect_controlled_write_request())
assert pending['continuation']['pending']
assert pending['host_result']['reason_code']=='USER_CANCELLED'
assert json.loads(session.begin_controlled_write_request('Blocked'))['reason']=='CONTINUATION_PENDING'
assert json.loads(session.inspect_controlled_write_request())==pending
'@,$sb2)
    $a.Execute(@'
hold_now[0]=130.0
assert s.controlled_writes.handoff.inspect()['pending']
s.controlled_writes.handoff.check()
'@,$sa)
    $c.Execute(@'
expired=json.loads(session.inspect_controlled_write_request())
assert expired['continuation']['last']['reason']=='CONTINUATION_HOLD_EXPIRED'
assert expired['state']=='CANCELLED'
assert expired['host_result']==pending['host_result']
'@,$sb2)
    $a.Execute(@'
# A later host callback still sees the pair consumed before the Dev inspection.
assert ('native_response','native_call') in h.seen
s.panel._provider_state.active=dict(request_id='later_transport',operation='agent_turn')
s.ai.turn=dict(request_id='later_transport',key=s.document_identity,
              generation=s.context_generation,selection=s.selection_generation,used=False)
ticket=h.open_transport(s.panel._provider_state.active,'fixture-model')
try:
    h.bind_response(ticket,dict(protocol_version=1,request_id='later_transport',ok=True,
        provider='openai',model='fixture-model',text=None,error=None,state='TOOL_REQUEST',
        tool_call=dict(name='set_selected_pipe_test_text',call_id='native_call',arguments=dict(value='Native')),
        provider_state=dict(response_id='later_response',model='fixture-model')))
    raise AssertionError('Duplicate call accepted')
except ValueError as error:
    assert str(error)=='PROVIDER_REPLAY_OR_CAPACITY'
assert ('later_response','native_call') not in h.seen
'@,$sa)
    $c.Execute(@'
assert json.loads(session.inspect_controlled_write_request())['host_result']==expired['host_result']
'@,$sb2)
    Write-Output 'PASS: 17 additional 003A real-session cross-engine assertions; no transport/mutation'
    $a.Execute(@'
# 003B-1: readiness and injected response binding owned entirely by engine A.
from bimcode_ai_pane.provider_write_adapter import Adapter, Launch
adapter=s.controlled_writes.adapter
assert type(adapter) is Adapter
active=dict(request_id='adapter_ready',operation='readiness')
s.panel._provider_state.active=active
adapter.remember_readiness(active,dict(protocol_version=1,request_id='adapter_ready',
    ok=True,provider='openai',model='fixture-model',text='READY',error=None))
active=dict(request_id='adapter_transport',operation='agent_turn')
s.panel._provider_state.active=active
s.ai.turn=dict(request_id='adapter_transport',key=s.document_identity,
    generation=s.context_generation,selection=s.selection_generation,used=False)
results=[]
def offline_transport(payload,callback):
    assert adapter.outstanding is not None
    assert payload is not active
    callback(dict(protocol_version=1,request_id='adapter_transport',ok=True,provider='openai',
        model='fixture-model',text=None,error=None,state='TOOL_REQUEST',
        tool_call=dict(name='set_selected_pipe_test_text',call_id='adapter_call',arguments=dict(value='Native')),
        provider_state=dict(response_id='adapter_response',model='fixture-model')))
launch=adapter.launch(active,offline_transport,results.append)
assert type(launch) is Launch
assert results[0].state=='TRUSTED_PROVIDER_BINDING_READY'
assert results[0].binding is h.binding
assert h.pending is None
assert s.write_admission.active is None
assert ('adapter_response','adapter_call') in h.seen
'@,$sa)
    $c.Execute(@'
# Dev engine receives only the existing serialized inspection, no adapter/ticket.
assert json.loads(session.inspect_controlled_write_request())['host_result']==expired['host_result']
'@,$sb2)
    Write-Output 'PASS: 10 additional 003B-1 persistent adapter assertions; binding only'
    $a.Execute(@'
# 003B-2A: all identity-sensitive authority remains in persistent engine A.
from bimcode_ai_pane.provider_write_transfer import Transfer, Reservation
transfer=s.controlled_writes.transfer
assert type(transfer) is Transfer
assert transfer.reserve()['state']=='PROVIDER_TURN_RESERVED'
assert type(transfer.reservation) is Reservation
before=s.write_admission.active
assert before is transfer.reservation.owner and type(before) is Owner
assert transfer.transfer()['state']=='CONTROLLED_WRITE_OWNER_TRANSFERRED'
assert s.write_admission.active is transfer.transferred
assert s.ai.turn is transfer.reservation.evidence[0].ticket.turn
assert transfer.adopt()['state']=='TRANSFERRED_OWNER_ADOPTED'
assert s.controlled_writes.dispatcher.owner is transfer.transferred
assert s.controlled_writes.dispatcher.used and s.controlled_writes.dispatcher.preview_json is None
'@,$sa)
    $c.Execute(@'
owned=json.loads(session.inspect_controlled_write_request())
assert owned['busy'] and owned['host_result'] is None
assert json.loads(session.begin_controlled_write_request('Competing'))['reason']=='EXECUTION_BUSY'
'@,$sb2)
    $a.Execute(@'
s.write_gate.cleanup('DOCUMENT_CLOSE')
assert s.write_admission.active is None
try:
    transfer.adopt()
    raise AssertionError('Invalidated adoption accepted')
except ValueError:
    pass
'@,$sa)
    Write-Output 'PASS: 14 additional 003B-2A cross-engine ownership assertions; no preview/execution'
    $a.Execute(@'
# FIX-001: contention retains safety in the persistent authority only.
m=s.write_admission
held=m.acquire('HUMAN_DEV_WRITE','safety','safety','doc',str(id(s)),1)
# Existing AI turn blocks admission; use the already-owned scalar-free manager
# in isolation while keeping inspection on the actual persistent PaneSession.
if held is None:
    s.ai.turn=None
    held=m.acquire('HUMAN_DEV_WRITE','safety','safety','doc',str(id(s)),1)
assert held is not None
m._lock.acquire(False)
try:
    assert not m.cleanup(held,'PANE_DISPOSAL',transaction_unresolved=True,evidence_source=m)
    assert m.safety_locked
finally:
    m._lock.release()
assert not m.release(held,'ORDINARY')
'@,$sa)
    $c.Execute(@'
safety=json.loads(session.inspect_controlled_write_request())['admission_safety']
assert safety['pending_cleanup'] and safety['retained_safety_lock']
assert safety['cleanup_reason']=='PANE_DISPOSAL' and safety['requires_intervention']
# Editing this deserialized copy cannot affect the persistent authority.
safety['retained_safety_lock']=False
assert json.loads(session.inspect_controlled_write_request())['admission_safety']['retained_safety_lock']
'@,$sb2)
    $a.Execute(@'
assert m.reconcile_cleanup(held,executor_quiescent=True)
assert m.active is None and m.safety_locked
assert not m.inspect_safety()['pending_cleanup']
assert not m.resolve_safety(False)
assert not m.resolve_safety(True)
ticket=m.resolution_ticket(m,held)
assert m.resolve_safety(True,ticket)
'@,$sa)
    $c.Execute(@'
snapshot=json.loads(session.inspect_controlled_write_request())['admission_safety']
assert snapshot['owner_state']=='QUIESCENT' and not snapshot['owner_present']
assert snapshot['safety_evidence_generation'] >= 1
assert 'execution_active' not in snapshot
'@,$sb2)
    $a.Execute(@'
m.retain_safety(True,m,held,'NEW')
assert not m.resolve_safety(True,ticket)
assert m.safety_locked
'@,$sa)
    Write-Output 'PASS: 12 additional FIX-001 persistent safety/Dev inspection assertions'
    Write-Output 'PASS: 7 additional FIX-002 pure snapshot/evidence authority assertions'
    $a.Execute(@'
class BrokenCleanup(object):
    @property
    def owner(self):
        raise AttributeError('missing owner')
    def cleanup(self, *args):
        raise ValueError('missing evidence')
before=m.inspect_safety()['safety_evidence_generation']
s.write_gate.lifecycle=BrokenCleanup()
s.write_gate.cleanup('PANE_DISPOSAL')
assert m.safety_locked
assert m.inspect_safety()['safety_evidence_generation']==before+1
s.write_gate.cleanup('PANE_DISPOSAL')
assert m.inspect_safety()['safety_evidence_generation']==before+1
'@,$sa)
    $c.Execute(@'
first=json.loads(session.inspect_controlled_write_request())['admission_safety']
assert first['retained_safety_lock'] and first['requires_intervention']
assert first==json.loads(session.inspect_controlled_write_request())['admission_safety']
'@,$sb2)
    Write-Output 'PASS: 5 additional FIX-003 persistent cleanup exception assertions'
    $checks=$sb.GetVariable('count')
    Write-Output "PASS: persistent IronPython engine plus two Dev engines; $checks counted boundary assertions; 29 additional session/stale-class/identity/lifecycle assertions; actual PaneSession API and Cancel passed; old Owner failure still rejected; stale class alternative reproduced (not live attribution)"
} finally { [IO.File]::Delete($archive) }
