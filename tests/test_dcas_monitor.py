import copy
from datetime import date
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError

spec=importlib.util.spec_from_file_location('monitor',Path(__file__).resolve().parents[1]/'scripts/dcas_monitor.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
CFG={'first_name':'ALEX','last_name':'EXAMPLE','exam_no':'4034','title_code':'13621','list_no':'123.500'}
def row(cert='80001',seq='3',expiry='2026-11-30T00:00:00.000'):
 return {'exam_no':'04034','list_title_code':'13621','list_no':'123.5','first_name':'ALEX','last_name':'EXAMPLE','cert_issue_no':cert,'cert_seq_no':seq,'cert_date':'2026-10-02T00:00:00.000','cert_expiration_date':expiry,'list_agency_code':'000','list_agency_desc':'OPEN COMPETITIVE'}
def snap(rows=None):
 rr=rows if rows is not None else [row()]
 return {'personal_rows':copy.deepcopy(rr),'coverage_rows':[{k:v for k,v in r.items() if k not in ['first_name','last_name']} for r in rr],'active_rows':[],
 'sources':{'personal':{'selected_fields':m.CERT_FIELDS},'coverage':{'selected_fields':m.CERT_FIELDS}}}
class FakeClient(m.Client):
 def __init__(self,drift=False,short=False):self.calls=[];self.metas=0;self.drift=drift;self.short=short
 def metadata(self,ds):
  self.metas+=1
  return {'columns':[{'fieldName':x} for x in m.CERT_FIELDS.split(',')],'rowsUpdatedAt':2 if self.drift and self.metas>1 else 1}
 def get(self,url,params=None):
  self.calls.append(params)
  if params['$select']=='count(*) as total':return [{'total':'3'}]
  rows=[row('80001'),row('80002'),row('80003')]
  return rows[params['$offset']:params['$offset']+(1 if self.short else params['$limit'])]
class SnapshotClient:
 def __init__(self,snapshot):self.s=snapshot
 def fetch(self,ds,where,fields,order):
  data=self.s['active_rows'] if ds==m.ACTIVE else self.s['personal_rows'] if "first_name=" in where else self.s['coverage_rows']
  return copy.deepcopy(data),{'rows_updated_at':1,'selected_fields':fields,'url':m.BASE+'/resource/'+ds+'.json'}
 def metadata(self,ds):return {'rowsUpdatedAt':1}
class Tests(unittest.TestCase):
 def test_pagination_and_exact_count_predicate(self):
  c=FakeClient();rows,e=c.fetch(m.CERT,'same predicate',m.CERT_FIELDS,m.ORDER,page_size=2)
  self.assertEqual(len(rows),3);self.assertEqual(e['count_before'],e['count_after'])
  self.assertEqual([x['$offset'] for x in c.calls if '$offset' in x],[0,2])
  self.assertTrue(all(x['$where']=='same predicate' for x in c.calls))
 def test_timestamp_drift_rejected_with_same_count(self):
  with self.assertRaisesRegex(m.VerificationError,'changed'):FakeClient(drift=True).fetch(m.CERT,'x',m.CERT_FIELDS,m.ORDER,page_size=2)
 def test_short_page_rejected(self):
  with self.assertRaisesRegex(m.VerificationError,'page'):FakeClient(short=True).fetch(m.CERT,'x',m.CERT_FIELDS,m.ORDER,page_size=2)
 def test_identity_and_leading_zero_decimal(self):
  cfg=m.validate_config(CFG);m.validate_rows([row()],cfg,True)
  self.assertIn("'04034'",m.predicates(cfg)[0]);self.assertIn('list_no=123.500',m.predicates(cfg)[1])
  r=row();r['list_title_code']='99999'
  with self.assertRaises(m.VerificationError):m.validate_rows([r],cfg,True)
  a=row();b=row();b['mi']='B'
  with self.assertRaisesRegex(m.VerificationError,'Ambiguous'):m.validate_rows([a,b],cfg,True)
 def test_current_ties_unknown_and_expiry_today(self):
  rows=[row(),row('80002',expiry='2026-10-24'),row('80003',seq='1',expiry=''),row('80004',seq='1',expiry='2026-10-23')]
  a=m.analyses(snap(rows),m.validate_config(CFG),date(2026,10,24))
  self.assertEqual(a['current_minimum'],'3');self.assertEqual(len(a['current_minimum_ties']),2)
  self.assertEqual(len(a['unknown_expiry_rows']),1)
  self.assertTrue(all(x['requesting_agency']['status']=='unverified' for x in a['current_minimum_ties']))
 def test_within_certificate_change_and_coverage(self):
  old=snap();new=snap([row(seq='2')]);events=m.differences(old,new)
  self.assertEqual(len(events),2);self.assertTrue(all(e['kind']=='certificate_changed' for e in events))
 def test_blank_expiry_becomes_observed(self):
  old=snap();old['personal_rows'][0].pop('cert_expiration_date');new=snap()
  self.assertTrue(m.differences(old,new))
 def test_added_field_baseline_not_change(self):
  old=snap();new=snap();old['sources']['personal']['selected_fields']=m.CERT_FIELDS.replace(',salary','')
  new['personal_rows'][0]['salary']='123'
  self.assertEqual(m.differences(old,new),[])
 def test_calendar_reissue_history(self):
  r=row();r['cert_date']='2025-01-01';r['reissue_date']='2026-10-01'
  a=m.analyses(snap([r]),m.validate_config(CFG),date(2026,10,24))
  self.assertEqual(len(a['older_reissued_in_month']),1);self.assertEqual(a['recent_month'],[])
  self.assertEqual(m.shift(date(2024,3,31),months=1),date(2024,2,29))
 def test_baseline_silent_dedup_and_failure_preserves_state(self):
  with tempfile.TemporaryDirectory() as td:
   state=Path(td)/'state.json';report=Path(td)/'report.json'
   self.assertEqual(m.run(CFG,state,report,SnapshotClient(snap()),date(2026,10,24)),'')
   changed=snap([row(seq='2')]);output=m.run(CFG,state,report,SnapshotClient(changed),date(2026,10,24))
   self.assertIn('Verified material differences',output)
   self.assertEqual(m.run(CFG,state,report,SnapshotClient(changed),date(2026,10,24)),'')
   before=state.read_bytes()
   class Broken:
    def fetch(self,*args):raise m.VerificationError('HTTP 503')
   with self.assertRaises(m.VerificationError):m.run(CFG,state,report,Broken(),date(2026,10,24))
   self.assertEqual(before,state.read_bytes());self.assertEqual(state.stat().st_mode & 0o777,0o600)
 def test_scope_mismatch_and_lock(self):
  with tempfile.TemporaryDirectory() as td:
   state=Path(td)/'state.json';m.run(CFG,state,None,SnapshotClient(snap()),date(2026,10,24))
   wrong=dict(CFG,list_no='999')
   with self.assertRaisesRegex(m.VerificationError,'scope'):m.run(wrong,state,None,SnapshotClient(snap()),date(2026,10,24))
   with m.state_lock(state):
    with self.assertRaisesRegex(m.VerificationError,'lock'):m.run(CFG,state,None,SnapshotClient(snap()),date(2026,10,24))
 def test_transient_retry_and_400_no_retry(self):
  attempts=[];delays=[]
  class Response:
   status=200
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,*args):return b'[]'
  def opener(req,timeout):
   attempts.append(1)
   if len(attempts)==1:raise HTTPError(req.full_url,503,'busy',{},None)
   return Response()
  self.assertEqual(m.Client(opener=opener,sleeper=delays.append).get(m.BASE),[])
  self.assertEqual(len(attempts),2);self.assertEqual(delays,[1])
  def bad(req,timeout):raise HTTPError(req.full_url,400,'bad',{},None)
  with self.assertRaisesRegex(m.VerificationError,'400'):m.Client(opener=bad,sleeper=lambda _:self.fail('retry')).get(m.BASE)
 def test_unofficial_agency_evidence_rejected(self):
  cfg=dict(CFG,agency_links=[{'cert_issue_no':'80001','agency_name':'Example','source_url':'https://example.com','verified_at':'2026-10-24'}])
  with self.assertRaises(m.VerificationError):m.validate_config(cfg)
 def test_verified_notice_changed_and_deduplicated(self):
  with tempfile.TemporaryDirectory() as td:
   state=Path(td)/'state.json'
   m.run(CFG,state,None,SnapshotClient(snap()),date(2026,10,24))
   cfg=dict(CFG,list_notices=[{'notice_id':'sample','kind':'extension','effective_date':'2026-10-24','verified_at':'2026-10-24','source_url':'https://www.nyc.gov/example-notice'}])
   output=m.run(cfg,state,None,SnapshotClient(snap()),date(2026,10,24))
   self.assertIn('host_verified_official_notice',output)
   self.assertEqual(m.run(cfg,state,None,SnapshotClient(snap()),date(2026,10,24)),'')
 def test_legacy_migration_preserves_history(self):
  with tempfile.TemporaryDirectory() as td:
   source=Path(td)/'legacy.json';state=Path(td)/'state.json'
   legacy={'queried_at':'2026-10-23T12:00:00+00:00','reported_events':[{'event_key':'sample'}],
    'personal_tracking':{'checkpoint':{'status':'ok','agency_scope':'all','queried_at':'2026-10-23T12:00:00+00:00','as_of':'2026-10-23','exam':'4034','title_code':'13621','all_personal_rows':[row()],'sources':{'certifications':{}}},
     'active_candidate_observation':{'rows':[],'metadata':{}},
     'coverage_checkpoint':{'queried_at':'2026-10-23T12:00:00+00:00','sources':{'certifications':{}},'snapshot':{'certificates':{'sample':{'fields':{k:[v] for k,v in row().items() if k not in ['first_name','last_name','list_no','cert_seq_no']},'sequence_pairs':[['123.5','3']]}}}}}}
   source.write_text(json.dumps(legacy));m.migrate_legacy(CFG,source,state)
   imported=json.loads(state.read_text());self.assertEqual(imported['legacy_notified_events'],legacy['reported_events'])
   self.assertFalse(m.differences(imported['snapshot'],snap()))
   self.assertEqual(m.run(CFG,state,None,SnapshotClient(snap()),date(2026,10,24)),'')
 def test_repeat_transition_is_a_new_observation(self):
  with tempfile.TemporaryDirectory() as td:
   state=Path(td)/'state.json'
   for index,seq in enumerate(['3','2','3','2']):
    output=m.run(CFG,state,None,SnapshotClient(snap([row(seq=seq)])),date(2026,10,24))
    self.assertEqual(bool(output),index>0)
 def test_null_mi_and_salary_only(self):
  r=row();r['mi']=None;m.validate_rows([r],m.validate_config(CFG),True)
  old=snap();new=snap();old['personal_rows'][0]['salary']='100';new['personal_rows'][0]['salary']='101'
  self.assertEqual(m.differences(old,new),[])
 def test_new_verified_agency_association_emits(self):
  with tempfile.TemporaryDirectory() as td:
   state=Path(td)/'state.json';m.run(CFG,state,None,SnapshotClient(snap()),date(2026,10,24))
   cfg=dict(CFG,agency_links=[{'cert_issue_no':'80001','agency_name':'Example agency','source_url':'https://www.nyc.gov/example','verified_at':'2026-10-24'}],focus_agencies=['Example agency'])
   self.assertIn('host_verified_agency_association_changed',m.run(cfg,state,None,SnapshotClient(snap()),date(2026,10,24)))
   self.assertEqual(m.run(cfg,state,None,SnapshotClient(snap()),date(2026,10,24)),'')
 def test_missing_sequence_does_not_prove_global_minimum(self):
  arow=row('80002');arow.pop('cert_seq_no')
  a=m.analyses(snap([row(),arow]),m.validate_config(CFG),date(2026,10,24))
  self.assertIsNone(a['current_minimum']);self.assertEqual(a['minimum_among_known_sequences'],'3')
  self.assertFalse(a['dated_minimum_complete'])
 def test_personal_observation_history_retained(self):
  with tempfile.TemporaryDirectory() as td:
   state=Path(td)/'state.json';m.run(CFG,state,None,SnapshotClient(snap()),date(2026,10,23))
   m.run(CFG,state,None,SnapshotClient(snap([row(seq='2')])),date(2026,10,24))
   history=json.loads(state.read_text())['personal_observations']
   self.assertEqual(len(history),2);self.assertEqual(history[0]['personal_rows'][0]['cert_seq_no'],'3')
   self.assertEqual(history[1]['personal_rows'][0]['cert_seq_no'],'2')
if __name__=='__main__':unittest.main()
