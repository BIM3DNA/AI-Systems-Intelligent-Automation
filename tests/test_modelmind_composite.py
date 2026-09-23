"""Offline M3F snapshot/fan-out probes; no network or real Revit objects."""
import copy
import itertools
import json
import types
import unittest
from unittest.mock import Mock, patch
import test_modelmind_headless as headless
import test_bimcode_ai_tool as old
import test_bimcode_piping_ai_tools as piping
import modelmind_composite as composite


class CompositeTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.effects = {}
        owner = self

        class Worker:
            def _mep_ro_001_id_value(self, ident): return ident
            def _mep_ro_001_id_text(self, ident): return str(ident)
            def _mep_ro_v1_active_view_type(self): return 'ThreeD'
            def _piping_ro_001_scope_kind(self, element): return 'SUPPORTED_PIPE' if element.kind == 'PIPING' else 'OTHER'
            def _hvac_ro_001_scope_kind(self, element): return 'SUPPORTED_DUCT' if element.kind == 'HVAC' else 'OTHER'
            def _electrical_ro_001_scope_kind(self, element): return ('SCOPE', element.profile if element.kind == 'ELECTRICAL' else None)
            def _mep_ro_001_element_record(self, element):
                return dict(element=element, element_id=str(element.id), category_id=element.kind, category_name=element.kind)

        self.module = types.SimpleNamespace(OllamaAIChat=Worker, doc=None, uidoc=None,
            _document_title=lambda d: 'Test', _active_view_title=lambda d, u: 'View')
        for specialty, metadata, method in composite.PLAN:
            action = specialty + '-RO-001-A01'
            setattr(self.module, metadata, {'summary': (action, 'canonical')})
            def builder(worker, prompt, key, snapshot, specialty=specialty, action=action):
                owner.calls.append((specialty, copy.copy(snapshot)))
                effect = owner.effects.get(specialty)
                if isinstance(effect, Exception): raise effect
                if callable(effect): return effect(snapshot)
                return effect or dict(action_id=action, classification=specialty+'_SELECTION_SUMMARY_OK',
                    reason_code='COMPLETE', summary=['Authoritative '+specialty], warnings=['warning'],
                    selected_reference_count=len(snapshot['selected_ids']), tables=[['Records',['ID'],[[r['element_id']] for r in snapshot['records']]]])
            setattr(Worker, method, builder)
        self.doc, self.uidoc = headless.context()
        self.elements = {}
        self.doc.GetElement = lambda ident: self.elements.get(ident)
        self.ids = []
        self.uidoc.Selection.GetElementIds = Mock(side_effect=lambda: list(self.ids))
        self.guard = Mock(return_value=True)
        self.loader = patch.object(composite.backend, '_load_backend', return_value=self.module)
        self.loader.start(); self.addCleanup(self.loader.stop)

    def select(self, kinds):
        self.ids = list(range(1,len(kinds)+1))
        self.elements = {i: types.SimpleNamespace(id=i,kind=k,profile='EQUIPMENT_PROFILE' if k=='ELECTRICAL' else None)
                         for i,k in zip(self.ids,kinds) if k != 'UNRESOLVED'}

    def run_result(self): return composite.execute(self.doc,self.uidoc,'a'*32,self.guard)

    def test_all_supported_combinations_and_partition(self):
        for n in (1,2,3):
            for kinds in itertools.combinations(('PIPING','HVAC','ELECTRICAL'),n):
                self.calls=[];self.select(kinds);self.uidoc.Selection.GetElementIds.reset_mock()
                r=self.run_result()
                self.assertEqual(r['classification'],'MEP_MULTI_SELECTION_SUMMARY_OK')
                self.assertEqual(r['supported_reference_count'],n)
                self.assertEqual([s for s,_ in self.calls],list(kinds))
                self.assertEqual(self.uidoc.Selection.GetElementIds.call_count,2) # capture + integrity only
                for specialty,snapshot in self.calls:
                    self.assertTrue(all(x['element'].kind==specialty for x in snapshot['records']))
                    self.assertEqual(snapshot['selected_id_texts'],[str(i) for i in snapshot['selected_ids']])
                self.assertEqual(self.ids,list(range(1,n+1)))

    def test_device_profile(self):
        self.select(['ELECTRICAL']);self.elements[1].profile='DEVICE_PROFILE'
        self.assertEqual(self.run_result()['classification'],'MEP_MULTI_SELECTION_SUMMARY_OK')

    def test_empty_unsupported_unresolved(self):
        for kinds,reason in (([],'NO_ELEMENTS_SELECTED'),(['OTHER'],'NO_SUPPORTED_SELECTED_ELEMENTS'),
                             (['UNRESOLVED'],'SELECTION_UNREADABLE'),(['PIPING','UNRESOLVED'],'SELECTION_UNREADABLE')):
            self.calls=[];self.select(kinds);r=self.run_result()
            self.assertEqual(r['reason_code'],reason);self.assertEqual(self.calls,[])
            self.assertEqual(r['classification'],'MEP_MULTI_SELECTION_NOT_READY')
            if 'PIPING' in kinds:
                self.assertTrue(r['specialties']['PIPING']['present'])
                self.assertEqual(r['specialties']['PIPING']['execution_state'],'NOT_EVALUATED')

    def test_unsupported_partial(self):
        self.select(['PIPING','OTHER']);r=self.run_result()
        self.assertEqual(r['reason_code'],'UNSUPPORTED_ELEMENTS_PRESENT')
        self.assertEqual(r['unsupported_scope']['count'],1)
        self.assertEqual(len(self.calls[0][1]['records']),1)

    def test_failure_permutations_no_retry(self):
        for failed in ('PIPING','HVAC','ELECTRICAL'):
            self.select(['PIPING','HVAC','ELECTRICAL']);self.calls=[];self.effects={failed:RuntimeError('private')}
            r=self.run_result();self.assertEqual(r['reason_code'],'SUBACTION_FAILED')
            self.assertEqual(len(self.calls),3);self.assertTrue(r['partial'])
            self.assertEqual(r['specialties'][failed]['error_code'],'HEADLESS_EXECUTION_FAILED')
            self.assertNotIn('private',json.dumps(r))

    def test_all_children_failed(self):
        self.select(['PIPING']);self.effects={'PIPING':RuntimeError()}
        self.assertEqual(self.run_result()['reason_code'],'NO_USABLE_SPECIALTY_RESULT')

    def test_stale_before_and_during_discards(self):
        for failure_call in range(1,7):
            self.select(['PIPING','HVAC']);self.guard.reset_mock()
            self.guard.side_effect=lambda: self.guard.call_count != failure_call
            r=self.run_result();self.assertEqual(r['reason_code'],'STALE_CONTEXT')
            self.assertEqual(r['sub_actions'],[])
            self.assertTrue(all(c['result'] is None for c in r['specialties'].values()))

    def test_selection_drift(self):
        self.select(['PIPING'])
        self.uidoc.Selection.GetElementIds.side_effect=[[1],[2]]
        self.assertEqual(self.run_result()['reason_code'],'STALE_CONTEXT')

    def test_lock_and_context_restoration(self):
        self.select(['PIPING']);composite.backend._EXECUTION_LOCK.acquire()
        try: self.assertEqual(self.run_result()['reason_code'],'EXECUTION_BUSY')
        finally: composite.backend._EXECUTION_LOCK.release()
        self.effects={'PIPING':RuntimeError()};self.run_result()
        self.assertIsNone(self.module.doc);self.assertIsNone(self.module.uidoc)
        self.assertTrue(composite.backend._EXECUTION_LOCK.acquire(False));composite.backend._EXECUTION_LOCK.release()

    def test_admission_bounds(self):
        for n in (599,600,601):
            self.select(['OTHER']*n);self.calls=[];r=self.run_result()
            self.assertEqual(r['reason_code'],'SELECTION_LIMIT_EXCEEDED' if n==601 else 'NO_SUPPORTED_SELECTED_ELEMENTS')
            self.assertEqual(self.calls,[])

    def test_projection_caps_do_not_change_semantics(self):
        self.select(['PIPING']);r=self.run_result()['specialties']['PIPING']['result']
        r['tables'][0][2]*=100;r['warnings']*=40
        bounded=composite.bounded_child(r,13,4)
        self.assertEqual(bounded['classification'],r['classification'])
        self.assertEqual(bounded['transport_omissions']['warnings'],10)
        self.assertEqual(bounded['transport_omissions']['tables'][0]['rows'],87)
        self.assertEqual(bounded['summary'],r['summary'])

    def test_oversized_core_rejected(self):
        with self.assertRaises(composite.backend.ProjectionError):
            composite.bounded_child(dict(summary=['x'*8000]*3),13,4)

    def test_partial_child_classification(self):
        self.select(['PIPING']);self.effects['PIPING']=dict(action_id='PIPING-RO-001-A01',
            classification='PIPING_SELECTION_REPORT_PARTIAL',reason_code='PARTIAL_SCOPE_OR_READ',summary=['exact'])
        r=self.run_result();self.assertEqual(r['reason_code'],'SUBACTION_PARTIAL')
        self.assertEqual(r['specialties']['PIPING']['result']['summary'],['exact'])

    def test_advisory_deadline_skips_remaining_without_retry(self):
        self.select(['PIPING','HVAC'])
        clock=[0]
        def piping_result(snapshot):
            clock[0]=3
            return dict(action_id='PIPING-RO-001-A01', classification='PIPING_SELECTION_SUMMARY_OK', reason_code='COMPLETE')
        self.effects['PIPING']=piping_result
        with patch.object(composite.time,'time',side_effect=lambda:clock[0]):
            r=self.run_result()
        self.assertEqual(r['sub_actions'],['PIPING-RO-001-A01'])
        self.assertEqual(r['specialties']['HVAC']['reason_code'],'TIME_BUDGET_EXCEEDED')
        self.assertTrue(r['partial'])

    def test_transport_only_does_not_make_partial(self):
        self.select(['PIPING']*100)
        r=self.run_result()
        self.assertTrue(r['transport_truncated']);self.assertFalse(r['partial'])
        self.assertLessEqual(composite.size(r),80000)

    def test_invalid_document_and_unreadable_selection(self):
        self.doc.IsValidObject=False
        self.assertEqual(self.run_result()['reason_code'],'NO_VALID_DOCUMENT_CONTEXT')
        self.doc.IsValidObject=True
        self.uidoc.Selection.GetElementIds.side_effect=RuntimeError()
        self.assertEqual(self.run_result()['reason_code'],'SELECTION_UNREADABLE')
        self.assertEqual(self.calls,[])

    def test_warning_totals_and_unicode_budget(self):
        self.select(['PIPING'])
        self.effects['PIPING']=dict(action_id='PIPING-RO-001-A01',classification='PIPING_SELECTION_SUMMARY_OK',
            reason_code='COMPLETE',summary=['Exact \u20ac fact'],warnings=['\u20ac']*40)
        r=self.run_result();c=r['specialties']['PIPING']
        self.assertEqual(c['warnings_total'],40);self.assertEqual(len(c['warnings']),30)
        self.assertEqual(c['transport_omissions']['warnings'],10)
        self.assertFalse(r['partial']);self.assertTrue(r['transport_truncated'])
        self.assertEqual(c['result']['summary'],['Exact \u20ac fact'])

    def test_aggregate_table_and_sample_limits(self):
        self.select(['PIPING']*100+['HVAC']*100+['ELECTRICAL']*100+['OTHER']*40)
        r=self.run_result()
        tables=[t for c in r['specialties'].values() for t in c['result']['tables']]
        self.assertLessEqual(len(tables),12)
        self.assertLessEqual(sum(len(t[2]) for t in tables),40)
        self.assertEqual(r['unsupported_scope']['omitted_count'],10)
        self.assertEqual(r['resolved_selected_count'],340)
        self.assertEqual(r['supported_reference_count']+r['unsupported_reference_count'],340)

    def test_child_not_ready_and_failed_classification(self):
        for ending,reason in (('_NOT_READY','SUBACTION_NOT_READY'),('_FAILED','SUBACTION_FAILED')):
            self.select(['PIPING','HVAC'])
            self.effects['PIPING']=dict(classification='PIPING_SELECTION'+ending,reason_code='CHILD_REASON')
            r=self.run_result();self.assertEqual(r['reason_code'],reason)
            self.assertEqual(r['specialties']['PIPING']['reason_code'],'CHILD_REASON')
            self.assertIsNotNone(r['specialties']['HVAC']['result'])

    def test_empty_row_budget_has_explicit_omissions(self):
        result=composite.bounded_child(dict(tables=[['T',['H'],[['exact']]]]),0,0)
        self.assertEqual(result['tables'],[])
        self.assertEqual(result['transport_omissions']['tables'],[dict(index=0,title='T',rows=1)])

    def test_no_network_mutation_or_nested_execution(self):
        import ast
        import pathlib
        tree=ast.parse(pathlib.Path(composite.__file__).read_text())
        forbidden={'Transaction','TransactionGroup','SubTransaction','SetElementIds','Set','Delete','Create',
                   'ExternalEvent','Raise','execute_headless_modelmind_readonly','requests','subprocess','openai','socket'}
        names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
        names.update(n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute))
        self.assertFalse(names & forbidden)


class CoordinatorTests(unittest.TestCase):
    setUp=old.CoordinatorTests.setUp

    def response(self):
        r=old.intermediate();r['tool_call']['name']='summarize_selected_mep_elements'
        return r

    def test_one_event_no_nested_executor_and_single_use(self):
        with patch.object(composite,'execute',return_value=composite.envelope(old.RID)) as execute:
            self.coordinator.queue(self.response(),self.done)
            execute.assert_not_called()
            self.session.raise_ai_event.assert_called_once()
            self.coordinator.execute_approved(self.uiapp)
            execute.assert_called_once()
            self.assertTrue(execute.call_args.args[-1]())
            self.resolve_headless_modelmind_specialty.assert_not_called()
            self.execute_headless_modelmind_readonly.assert_not_called()
            self.coordinator.queue(self.response(),self.done)
            self.coordinator.execute_approved(self.uiapp)
            self.assertEqual(execute.call_count,1)
            self.assertEqual(self.done.call_args.args[0]['error']['code'],'AI_TOOL_LOOP_LIMIT')

    def test_all_host_guard_dimensions(self):
        for dimension in ('document','context','selection','request'):
            self.coordinator.clear();self.coordinator.begin(old.RID)
            def execute(doc,uidoc,rid,guard):
                self.assertTrue(guard())
                if dimension=='document':self.document_key.return_value=('other',)
                elif dimension=='context':self.session.context_generation+=1
                elif dimension=='selection':self.session.selection_generation+=1
                else:self.coordinator.turn=dict(self.coordinator.turn)
                self.assertFalse(guard())
                return composite.stop(composite.envelope(rid),'STALE_CONTEXT',True)
            self.document_key.return_value=self.session.document_identity
            with patch.object(composite,'execute',side_effect=execute):
                self.coordinator.queue(self.response(),self.done)
                self.coordinator.execute_approved(self.uiapp)
            self.assertEqual(self.done.call_args.args[0]['error']['code'],'STALE_CONTEXT')


class ProviderTests(unittest.TestCase):
    send=old.ProviderTests.send

    def test_fixed_schema_continuation_and_loop(self):
        name='summarize_selected_mep_elements'
        self.assertEqual(old.tool_protocol.ACTIONS[name],composite.ACTION)
        self.assertEqual(len(old.provider.TOOLS),13)
        t=next(t for t in old.provider.TOOLS if t['name']==name)
        self.assertTrue(t['strict']);self.assertEqual(t['parameters'],dict(type='object',properties={},required=[],additionalProperties=False))
        response=self.send([old.output_call(name=name)])
        req=old.request('tool_result',tool_call=response['tool_call'],provider_state=response['provider_state'],tool_result=composite.envelope(old.RID))
        self.assertEqual(self.send(req=req)['state'],'FINAL')
        args=self.client.responses.create.call_args.kwargs
        self.assertEqual((args['store'],args['tools'],args['tool_choice']),(False,[],'none'))
        self.assertEqual(self.send([old.output_call(name=name)],req=req)['error']['code'],'AI_TOOL_LOOP_LIMIT')

    def test_no_override_or_multiple_calls(self):
        name='summarize_selected_mep_elements'
        for key in ('action_id','specialties','element_ids','command'):
            self.assertEqual(self.send([old.output_call(name=name,arguments=json.dumps({key:[]}))])['error']['code'],'AI_TOOL_ARGUMENTS_INVALID')
        self.assertEqual(self.send([old.output_call(name=name),old.output_call()])['error']['code'],'AI_TOOL_LOOP_LIMIT')

    def test_visible_provenance(self):
        r=old.protocol.success(old.RID,'test','Explanation')
        r['tool_provenance']=dict(action_id=composite.ACTION,classification='TEST',reason_code='COMPLETE',sub_actions=['PIPING-RO-001-A01'])
        self.assertIn('PIPING-RO-001-A01',str(old.provider_ui.presentation(r)))

    def test_composite_result_rejects_child_override(self):
        for key,value in (('action_id','PIPING-RO-001-A04'),('specialty','HVAC')):
            r=composite.envelope(old.RID);r['specialties']['PIPING'][key]=value
            with self.assertRaises(old.tool_protocol.ToolError):old.tool_protocol.validate_composite(r)
        r=composite.envelope(old.RID);r['sub_actions']=['PIPING-RO-001-A01']
        with self.assertRaises(old.tool_protocol.ToolError):old.tool_protocol.validate_composite(r)


if __name__=='__main__':unittest.main()
