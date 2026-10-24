#!/usr/bin/env python3
"""Private, English-first DCAS monitor. Python standard library; official SODA2 only."""
import argparse
import calendar
from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

CERT = 'a9md-ynri'
ACTIVE = 'vx8i-nprf'
BASE = 'https://data.cityofnewyork.us'
CERT_FIELDS = ('exam_no,list_no,first_name,mi,last_name,list_agency_code,list_agency_desc,'
               'list_title_desc,cert_seq_no,request_date,salary,cert_issue_no,cert_date,'
               'reissue_date,cert_expiration_date,no_certified,no_requested,'
               'provisional_replacement,no_vacancies,list_title_code,sel_cert_description')
ACTIVE_FIELDS = ('exam_no,list_no,first_name,mi,last_name,list_title_code,list_title_desc,'
                 'adj_fa,group_no,established_date,anniversary_date,extension_date')
ORDER = 'cert_date DESC,cert_issue_no DESC,cert_seq_no ASC,:id DESC'
SOURCE_URLS = {'certifications': BASE+'/resource/'+CERT+'.json',
               'active': BASE+'/resource/'+ACTIVE+'.json'}
RETRYABLE = {408, 429, 500, 502, 503, 504}


class VerificationError(Exception):
    pass


def decimal(value):
    try:
        n = Decimal(str(value))
        if not n.is_finite():
            raise ValueError('nonfinite')
        return n
    except (InvalidOperation, ValueError):
        raise VerificationError('Invalid exact decimal value') from None


def day(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise VerificationError('Invalid official date') from None


def literal(value):
    return "'"+str(value).replace("'", "''")+"'"


def exam_forms(value):
    text = str(value).strip()
    if not text.isascii() or not text.isdigit():
        raise VerificationError('Exam must be numeric text')
    stripped = text.lstrip('0') or '0'
    return sorted({text, stripped, stripped.zfill(5)})


def canonical_exam(value):
    return str(value).lstrip('0') or '0'


def validate_config(config):
    cfg = dict(config)
    for field in ('first_name', 'last_name', 'exam_no', 'title_code', 'list_no'):
        if not isinstance(cfg.get(field), str) or not cfg[field].strip():
            raise VerificationError('Private config requires text field: '+field)
        cfg[field] = cfg[field].strip()
    cfg['first_name'] = cfg['first_name'].upper()
    cfg['last_name'] = cfg['last_name'].upper()
    exam_forms(cfg['exam_no'])
    decimal(cfg['list_no'])
    if cfg.get('mi') is not None:
        cfg['mi'] = str(cfg['mi']).strip().upper()
    cfg.setdefault('agency_links', [])
    cfg.setdefault('list_notices', [])
    for link in cfg['agency_links']:
        host = urlsplit(link.get('source_url', '')).hostname or ''
        if urlsplit(link.get('source_url', '')).scheme != 'https' or not (
                host == 'nyc.gov' or host.endswith('.nyc.gov') or host == 'data.cityofnewyork.us'):
            raise VerificationError('Agency associations require official NYC HTTPS evidence')
        if not link.get('cert_issue_no') or not link.get('agency_name') or not day(link.get('verified_at')):
            raise VerificationError('Agency association needs cert, name and verification date')
    for notice in cfg['list_notices']:
        host=urlsplit(notice.get('source_url','')).hostname or ''
        if notice.get('kind') not in ('termination','extension') or not notice.get('notice_id') or not day(notice.get('verified_at')) or not day(notice.get('effective_date')) or urlsplit(notice.get('source_url','')).scheme!='https' or not (host=='nyc.gov' or host.endswith('.nyc.gov')):
            raise VerificationError('List notices need official NYC evidence, ID, kind and verified/effective dates')
    return cfg


def scope(config):
    return {k:config.get(k) for k in ('first_name','last_name','mi','exam_no','title_code','list_no')}


def normalized_scope(config):
    s = scope(config)
    s['exam_no'] = canonical_exam(s['exam_no'])
    s['list_no'] = str(decimal(s['list_no']).normalize())
    return s


def predicates(cfg):
    base = 'exam_no in('+','.join(literal(x) for x in exam_forms(cfg['exam_no']))+')'
    base += ' AND list_title_code='+literal(cfg['title_code'])
    person = base+' AND first_name='+literal(cfg['first_name'])+' AND last_name='+literal(cfg['last_name'])
    person += ' AND list_no='+str(decimal(cfg['list_no']))
    if cfg.get('mi') is not None:
        # Omitted MI and empty MI are distinct configuration choices.
        person += (' AND (mi IS NULL OR mi=\'\')' if not cfg['mi'] else ' AND mi='+literal(cfg['mi']))
    return base, person


class Client:
    def __init__(self, timeout=30, retries=3, opener=urlopen, sleeper=time.sleep):
        self.timeout, self.retries, self.opener, self.sleeper = timeout, retries, opener, sleeper

    def get(self, url, params=None):
        if params:
            url += '?'+urlencode(params)
        headers = {'Accept':'application/json','User-Agent':'nyc-dcas-cert-tracker/2.0'}
        token = os.environ.get('SODA_APP_TOKEN')
        if token:
            headers['X-App-Token'] = token
        for attempt in range(self.retries+1):
            try:
                with self.opener(Request(url, headers=headers), timeout=self.timeout) as response:
                    if response.status != 200:
                        raise VerificationError('Unexpected HTTP status '+str(response.status))
                    raw = response.read(32_000_001)
                if len(raw)>32_000_000:
                    raise VerificationError('Official response exceeds size limit')
                return json.loads(raw)
            except HTTPError as exc:
                if exc.code not in RETRYABLE or attempt == self.retries:
                    raise VerificationError('Official SODA2 HTTP '+str(exc.code)+
                                            ('; inspect official dataset metadata' if exc.code==400 else '')) from None
                after = exc.headers.get('Retry-After','')
                delay = min(int(after),30) if after.isdigit() else min(2**attempt,15)
            except (URLError, TimeoutError, OSError) as exc:
                if attempt == self.retries:
                    raise VerificationError('Official SODA2 transport error: '+str(exc)) from None
                delay = min(2**attempt,15)
            except (ValueError, UnicodeError):
                raise VerificationError('Malformed official JSON') from None
            self.sleeper(delay)

    def metadata(self, dataset):
        meta = self.get(BASE+'/api/views/'+dataset+'.json')
        if not isinstance(meta,dict) or not isinstance(meta.get('columns'),list) or 'rowsUpdatedAt' not in meta:
            raise VerificationError('Malformed official metadata')
        return meta

    def fetch(self, dataset, where, fields, order, page_size=1000, max_rows=100000):
        meta = self.metadata(dataset)
        available = {c.get('fieldName') for c in meta['columns']}
        missing = set(fields.split(','))-available
        if missing:
            raise VerificationError('Official schema missing fields: '+','.join(sorted(missing)))
        url = BASE+'/resource/'+dataset+'.json'
        def count():
            r = self.get(url, {'$where':where,'$select':'count(*) as total'})
            if not isinstance(r,list) or len(r)!=1 or not isinstance(r[0],dict) or not str(r[0].get('total','')).isdigit():
                raise VerificationError('Malformed official count')
            return int(r[0]['total'])
        before = count()
        if before>max_rows:
            raise VerificationError('Scope exceeds configured maximum rows')
        rows=[]
        for offset in range(0,before,page_size):
            batch=self.get(url,{'$where':where,'$select':fields,'$order':order,'$limit':page_size,'$offset':offset})
            if not isinstance(batch,list) or len(batch)!=min(page_size,before-offset) or any(not isinstance(r,dict) for r in batch):
                raise VerificationError('Incomplete or malformed official page')
            rows.extend(batch)
        after=count()
        end=self.metadata(dataset)
        if before!=after or len(rows)!=before or meta['rowsUpdatedAt']!=end['rowsUpdatedAt']:
            raise VerificationError('Official dataset changed during retrieval; observation discarded')
        # Projection must include sufficient identity fields to detect duplicate/missing pages.
        if len({json.dumps(r,sort_keys=True) for r in rows})!=len(rows):
            raise VerificationError('Duplicate projected rows; completeness cannot be established')
        return rows, {'url':url,'where':where,'selected_fields':fields,'order':order,
                      'count_before':before,'count_after':after,'fetched_rows':len(rows),
                      'page_size':page_size,'rows_updated_at':end['rowsUpdatedAt'],
                      'rows_updated_at_utc':datetime.fromtimestamp(end['rowsUpdatedAt'],timezone.utc).isoformat()}


def validate_rows(rows, cfg, personal=False):
    for r in rows:
        if str(r.get('exam_no')) not in exam_forms(cfg['exam_no']) or r.get('list_title_code')!=cfg['title_code']:
            raise VerificationError('Official response does not match exam/title scope')
        if personal and (str(r.get('first_name') or '').strip().upper()!=cfg['first_name'] or
                         str(r.get('last_name') or '').strip().upper()!=cfg['last_name'] or
                         decimal(r.get('list_no'))!=decimal(cfg['list_no']) or
                         (cfg.get('mi') is not None and str(r.get('mi') or '').strip().upper()!=cfg['mi'])):
            raise VerificationError('Official response does not match private identity')
    if personal and len({str(r.get('mi') or '').strip().upper() for r in rows})>1:
        raise VerificationError('Ambiguous candidate MI; do not merge identities')


def acquire(cfg, client):
    base, person=predicates(cfg)
    personal, pm=client.fetch(CERT,person,CERT_FIELDS,ORDER)
    active, am=client.fetch(ACTIVE,person,ACTIVE_FIELDS,'list_no ASC,:id DESC')
    fields=','.join(x for x in CERT_FIELDS.split(',') if x not in ('first_name','mi','last_name','salary','list_title_desc'))
    coverage, cm=client.fetch(CERT,base,fields,ORDER)
    validate_rows(personal,cfg,True);validate_rows(active,cfg,True);validate_rows(coverage,cfg)
    validate_rows(personal+active,cfg,True)
    for ds, evidences in ((CERT,[pm,cm]),(ACTIVE,[am])):
        latest=client.metadata(ds)['rowsUpdatedAt']
        if any(e['rows_updated_at']!=latest for e in evidences):
            raise VerificationError('Official dataset changed between queries; observation discarded')
    return {'personal_rows':personal,'active_rows':active,'coverage_rows':coverage,
            'sources':{'personal':pm,'active':am,'coverage':cm}}


def canonical_row(row):
    r={k:('' if v is None else str(v)) for k,v in row.items()}
    r['exam_no']=canonical_exam(r['exam_no'])
    for k in ('list_no','cert_seq_no','cert_issue_no'):
        if r.get(k):r[k]=str(decimal(r[k]).normalize())
    return r


def batch_key(row):
    return '|'.join((canonical_exam(row['exam_no']),row['list_title_code'],str(decimal(row['cert_issue_no']).normalize())))


def grouped(rows):
    groups={}
    for r in rows:groups.setdefault(batch_key(r),[]).append(canonical_row(r))
    return groups


def signature(rows, fields):
    return sorted(json.dumps({k:r.get(k,'') for k in fields},sort_keys=True) for r in rows)


def differences(old, new):
    events=[]
    for section in ('personal_rows','coverage_rows'):
        a,b=grouped(old[section]),grouped(new[section])
        for key in sorted(set(a)|set(b)):
            before,after=a.get(key,[]),b.get(key,[])
            # Optional new fields get a baseline; missing/null is blank within an observed field.
            if before and after:
                source='personal' if section=='personal_rows' else 'coverage'
                old_fields=old.get('sources',{}).get(source,{}).get('selected_fields')
                new_fields=new.get('sources',{}).get(source,{}).get('selected_fields')
                fields=(set(old_fields.split(',')) & set(new_fields.split(','))) if old_fields and new_fields else (set().union(*(set(r) for r in before)) & set().union(*(set(r) for r in after)))
                fields.discard('salary')
                if signature(before,fields)==signature(after,fields):continue
            elif not before and not after:continue
            kind='new_certificate' if not before else ('unverified_disappearance' if not after else 'certificate_changed')
            if section=='coverage_rows' and not a.get(key) and key not in grouped(new['personal_rows']):
                continue  # Monitor person-related new batches, not unrelated new certifications.
            if section=='coverage_rows' and key not in grouped(old['personal_rows']) and key not in grouped(new['personal_rows']):
                continue
            event={'section':section,'batch':key,'kind':kind,'old':before,'new':after}
            event['event_key']=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()
            events.append(event)
    a=[canonical_row(r) for r in old['active_rows']];b=[canonical_row(r) for r in new['active_rows']]
    fields=set().union(*(set(r) for r in a+b)) if a+b else set()
    if signature(a,fields)!=signature(b,fields):
        e={'section':'active_rows','kind':'active_observation_changed','old':a,'new':b}
        e['event_key']=hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest();events.append(e)
    return events


def shift(d, months=0, years=0):
    index=d.year*12+d.month-1-months-years*12;y,m=divmod(index,12);m+=1
    return date(y,m,min(d.day,calendar.monthrange(y,m)[1]))


def analyses(snapshot, cfg, as_of):
    rows=snapshot['personal_rows'];current=[];unknown=[]
    for r in rows:
        issued,expiry=day(r.get('cert_date')),day(r.get('cert_expiration_date'))
        if issued and issued<=as_of:
            if expiry is None:unknown.append(r)
            elif expiry>=as_of:current.append(r)
    seqs=[decimal(r['cert_seq_no']) for r in current if r.get('cert_seq_no')]
    known_minimum=min(seqs) if seqs else None
    missing_sequences=[r for r in current if not r.get('cert_seq_no')]
    minimum=known_minimum if not missing_sequences else None
    month,year=shift(as_of,months=1),shift(as_of,years=1)
    ordered=sorted(rows,key=lambda r:(r.get('cert_date',''),decimal(r['cert_issue_no']),decimal(r.get('cert_seq_no') or 0)))
    annual=[r for r in ordered if day(r.get('cert_date')) and year<=day(r['cert_date'])<=as_of]
    associations={str(decimal(x['cert_issue_no']).normalize()):x for x in cfg['agency_links']}
    def agency(r):
        evidence=associations.get(str(decimal(r['cert_issue_no']).normalize()))
        return {'name':evidence['agency_name'],'source_url':evidence['source_url'],'verified_at':evidence['verified_at'],'status':'host-verified official association'} if evidence else {'name':'Unverified requesting agency','status':'unverified'}
    histories={}
    for r in annual:
        association=agency(r)
        label=association['name'] if association['status']!='unverified' else 'Unverified requesting agency / Cert '+r['cert_issue_no']
        histories.setdefault(label,[]).append(r)
    summaries={}
    for name,rr in histories.items():
        enriched=[];previous=None
        for r in rr:
            different=previous is not None and r['cert_issue_no']!=previous['cert_issue_no']
            delta=str(decimal(r['cert_seq_no'])-decimal(previous['cert_seq_no'])) if different and r.get('cert_seq_no') and previous.get('cert_seq_no') else None
            enriched.append(dict(r,difference_from_previous_certificate=delta))
            previous=r
        nums=[decimal(r['cert_seq_no']) for r in rr if r.get('cert_seq_no')]
        summaries[name]={'rows':enriched,'first':rr[0].get('cert_seq_no'),'latest':rr[-1].get('cert_seq_no'),
                         'best':str(min(nums)) if nums else None,'worst':str(max(nums)) if nums else None,
                         'interpretation':'Across separate certificates; no within-certificate movement or hiring inference.'}
    focus={}
    for name in cfg.get('focus_agencies',[]):
        linked=[r for r in ordered if agency(r)['name']==name and agency(r)['status']!='unverified']
        focus[name]={'verified_personal_rows':linked,'status':'linked rows only; not comprehensive agency coverage' if linked else 'No independently linked personal certificates; agency coverage unverified'}
    return {'focus_agencies':focus,'current_minimum':str(minimum) if minimum is not None else None,
            'minimum_among_known_sequences':str(known_minimum) if known_minimum is not None else None,
            'dated_minimum_complete':not missing_sequences,
            'current_minimum_ties':[dict(r,requesting_agency=agency(r)) for r in current if r.get('cert_seq_no') and decimal(r['cert_seq_no'])==minimum],
            'current_rows':current,'unknown_expiry_rows':unknown,
            'current_missing_sequence':[r for r in current if not r.get('cert_seq_no')],
            'month_start':str(month),'recent_month':[r for r in ordered if day(r.get('cert_date')) and month<=day(r['cert_date'])<=as_of],
            'older_reissued_in_month':[r for r in ordered if day(r.get('cert_date')) and day(r['cert_date'])<month and day(r.get('reissue_date')) and month<=day(r['reissue_date'])<=as_of],
            'year_start':str(year),'annual_histories':summaries,
            'older_reissued_in_year':[r for r in ordered if day(r.get('cert_date')) and day(r['cert_date'])<year and day(r.get('reissue_date')) and year<=day(r['reissue_date'])<=as_of],
            'agency_associations':associations,'active_rows':snapshot['active_rows'],
            'identity_status':'matched' if rows or snapshot['active_rows'] else 'no matching official candidate rows',
            'official_list_notices':cfg['list_notices']}


def coverage_summary(rows):
    if not rows:return {'distinct_list_numbers':[],'min':None,'max':None}
    nums=sorted({decimal(r['list_no']) for r in rows})
    return {'distinct_count':len(nums),'min':str(min(nums)),'max':str(max(nums)),
            'distinct_list_numbers':[str(n) for n in nums],'continuous_coverage_assumed':False}


def report_text(report):
    a=report['analysis'];lines=['DCAS personal certification check — '+report['as_of'],
        'Observation: '+report['queried_at'],'Status: '+('Initial baseline; no change alert.' if report['initial_baseline'] else 'Verified material differences: '+str(len(report['events']))),
        'Current minimum Cert Seq No: '+str(a['current_minimum'])]
    for r in a['current_minimum_ties']:
        lines.append(' | '.join((r['requesting_agency']['name'],'Cert '+r['cert_issue_no'],'Seq '+r['cert_seq_no'],
            'request '+r.get('request_date',''),'issue '+r.get('cert_date',''),'reissue '+r.get('reissue_date',''),'expiry '+r.get('cert_expiration_date',''))))
    lines.append('Unknown-expiry records: '+str(len(a['unknown_expiry_rows'])))
    if a['current_missing_sequence']:
        lines.append('Global dated minimum unproved: some unexpired records lack Cert Seq No. Minimum among known sequences: '+str(a['minimum_among_known_sequences']))
    for e in report['events']:
        lines.append(json.dumps(e,ensure_ascii=False,sort_keys=True))
    lines.append('Agency focus: '+json.dumps(a['focus_agencies'],ensure_ascii=False))
    lines.append('Recent calendar month: '+json.dumps(a['recent_month'],ensure_ascii=False))
    lines.append('One-year issued-batch history (current source): '+json.dumps(a['annual_histories'],ensure_ascii=False))
    lines.append('Retained dated personal observations: '+json.dumps(a.get('retained_personal_observations',[]),ensure_ascii=False))
    lines.append('Active List observation: '+json.dumps(a['active_rows'],ensure_ascii=False))
    lines.append('Sources / dataset update timestamps: '+json.dumps(report['sources'],sort_keys=True))
    lines.append('Certification and sequence do not establish reachability, hire, Permanent Appointment or tie-breaker results. '
                 'Raw list-agency fields do not establish the requesting agency. Active disappearance/anniversary/extension fields require independent official confirmation of termination or extension.')
    return '\n'.join(lines)+'\n'


def write_private(path, data):
    dest=Path(path).expanduser();dest.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.dcas-',dir=dest.parent)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            f.write(data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        os.replace(tmp,dest);os.chmod(dest,0o600)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


@contextmanager
def state_lock(path):
    lock=Path(str(path)+'.lock');lock.parent.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise VerificationError('Another run or stale state lock exists; inspect before retrying') from None
    try:
        os.write(fd,str(os.getpid()).encode());os.close(fd);yield
    finally:lock.unlink(missing_ok=True)


def run(cfg, state_path, report_path, client, as_of, emit_baseline=False, digest=False):
    cfg=validate_config(cfg)
    with state_lock(state_path):
        old=json.loads(Path(state_path).read_text()) if Path(state_path).exists() else None
        if old and (old.get('schema_version')!=1 or old.get('scope')!=normalized_scope(cfg)):
            raise VerificationError('Checkpoint schema/scope mismatch; preserve state and migrate explicitly')
        snapshot=acquire(cfg,client)
        previous=old['snapshot'] if old else None
        events=differences(previous,snapshot) if previous else []
        if old:
            prior_notices={x['notice_id']:x for x in old.get('official_list_notices',[])}
            for notice in cfg['list_notices']:
                if notice!=prior_notices.get(notice['notice_id']):
                    event={'section':'official_list_notices','kind':'host_verified_official_notice','old':prior_notices.get(notice['notice_id']),'new':notice}
                    event['event_key']=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest();events.append(event)
        if old:
            prior_links={str(x['cert_issue_no']):x for x in old.get('official_agency_links',[])}
            for link in cfg['agency_links']:
                if link!=prior_links.get(str(link['cert_issue_no'])):
                    events.append({'section':'official_agency_links','kind':'host_verified_agency_association_changed','old':prior_links.get(str(link['cert_issue_no'])),'new':link})
        # Distinguish a later recurrence of a real transition from a delivery retry.
        for event in events:
            payload={k:v for k,v in event.items() if k!='event_key'}
            event['event_key']=hashlib.sha256(json.dumps({'previous_observation':old['queried_at'] if old else None,'event':payload},sort_keys=True).encode()).hexdigest()
        emitted=set(old.get('emitted_event_keys',[])) if old else set()
        events=[e for e in events if e['event_key'] not in emitted]
        # A disappearance is observable uncertainty, never verified removal/termination.
        for e in events:
            e['interpretation']='Unverified disappearance; reconfirm, no removal/hiring inference.' if e['kind']=='unverified_disappearance' else 'Official observation difference; no hiring inference.'
            if e.get('section')=='coverage_rows':
                e['old_coverage']=coverage_summary(e['old']);e['new_coverage']=coverage_summary(e['new'])
        analysis=analyses(snapshot,cfg,as_of)
        now=datetime.now(timezone.utc).isoformat()
        retained=list(old.get('personal_observations',[])) if old else []
        if old and not retained:
            retained=[{'observed_at':old['queried_at'],'as_of':old['as_of'],'personal_rows':old['snapshot']['personal_rows'],'active_rows':old['snapshot']['active_rows']}]
        observation={'observed_at':now,'as_of':str(as_of),'personal_rows':snapshot['personal_rows'],'active_rows':snapshot['active_rows']}
        if not retained or any(retained[-1][k]!=observation[k] for k in ('personal_rows','active_rows')):
            retained.append(observation)
        retained=[x for x in retained if day(x['as_of'])>=shift(as_of,years=1)]
        analysis['retained_personal_observations']=retained
        report={'as_of':str(as_of),'queried_at':now,'initial_baseline':old is None,
                'previous_successful_query_at':old.get('queried_at') if old else None,
                'sources':snapshot['sources'],'events':events,'analysis':analysis,'language':'en'}
        should_emit=bool(events) or digest or (old is None and emit_baseline)
        report['notification_emitted']=should_emit
        # Report-before-checkpoint: failed output writes never consume the successful baseline.
        if report_path:write_private(report_path,report)
        state={'schema_version':1,'scope':normalized_scope(cfg),'queried_at':now,'as_of':str(as_of),
               'snapshot':snapshot,'official_agency_links':cfg['agency_links'],'official_list_notices':cfg['list_notices'],'emitted_event_keys':sorted(emitted|{e['event_key'] for e in events}),
               'last_report':report,'personal_observations':retained,'legacy_notified_events':old.get('legacy_notified_events',[]) if old else []}
        write_private(state_path,state)
        return report_text(report) if should_emit else ''


def migrate_legacy(cfg, source_path, state_path):
    """Import the earlier private tracker checkpoint without publishing or resetting it."""
    cfg=validate_config(cfg)
    if Path(state_path).exists():raise VerificationError('Migration destination already exists')
    old=json.loads(Path(source_path).read_text())
    tracking=old.get('personal_tracking',{})
    person=tracking.get('checkpoint',{})
    coverage=tracking.get('coverage_checkpoint',{})
    active=tracking.get('active_candidate_observation',{})
    if person.get('status')!='ok' or person.get('agency_scope')!='all' or not person.get('queried_at') or not coverage.get('queried_at'):
        raise VerificationError('Legacy file lacks complete dated ALL-agency checkpoints')
    if canonical_exam(person.get('exam',''))!=canonical_exam(cfg['exam_no']) or person.get('title_code')!=cfg['title_code']:
        raise VerificationError('Legacy exam/title scope differs')
    rows=person.get('all_personal_rows',[]);ar=active.get('rows')
    if not rows or ar is None:raise VerificationError('Legacy identity/Active checkpoint unavailable')
    validate_rows(rows+ar,cfg,True)
    cr=[]
    for group in coverage['snapshot']['certificates'].values():
        fields=group['fields']
        if any(len(values)!=1 for values in fields.values()):
            raise VerificationError('Legacy aggregated fields are ambiguous; cannot reconstruct rows')
        for list_no,seq in group['sequence_pairs']:
            cr.append(dict({k:v[0] for k,v in fields.items()},list_no=list_no,cert_seq_no=seq))
    validate_rows(cr,cfg)
    selected=','.join(x for x in CERT_FIELDS.split(',') if x not in ('salary','list_title_desc'))
    snapshot={'personal_rows':rows,'active_rows':ar,'coverage_rows':cr,
              'sources':{'personal':dict(person['sources']['certifications'],selected_fields=selected),
                         'active':active['metadata'],
                         'coverage':dict(coverage['sources']['certifications'],selected_fields=selected)}}
    state={'schema_version':1,'scope':normalized_scope(cfg),'queried_at':old['queried_at'],
           'as_of':person['as_of'],'snapshot':snapshot,'official_list_notices':[],
           'emitted_event_keys':[], 'legacy_notified_events':old.get('reported_events',[]),
           'migration_note':'Imported verified legacy observations; no fresh-baseline alert. Raw agency fields do not verify requesting agency.'}
    with state_lock(state_path):write_private(state_path,state)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,help='Private JSON identity and official agency links')
    parser.add_argument('--state',required=True,help='Private durable checkpoint JSON')
    parser.add_argument('--report',help='Private complete JSON report, also on silent runs')
    parser.add_argument('--as-of',help='YYYY-MM-DD; defaults to America/New_York today')
    parser.add_argument('--migrate-from',help='Import the older private tracker JSON into a new state path before checking')
    parser.add_argument('--digest',action='store_true',help='Print full English report even without changes')
    parser.add_argument('--emit-baseline',action='store_true',help='Print first baseline (not a change alert)')
    args=parser.parse_args()
    try:
        paths=[str(Path(p).resolve()) for p in [args.config,args.state,args.report,args.migrate_from] if p]
        if len(paths)!=len(set(paths)):raise VerificationError('Config, state and report paths must differ')
        cfg=json.loads(Path(args.config).read_text())
        as_of=date.fromisoformat(args.as_of) if args.as_of else datetime.now(ZoneInfo('America/New_York')).date()
        if args.migrate_from:migrate_legacy(cfg,args.migrate_from,args.state)
        output=run(cfg,args.state,args.report,Client(),as_of,args.emit_baseline,args.digest)
        if output:print(output,end='')
        return 0
    except (VerificationError,ValueError,KeyError,OSError) as exc:
        print('Verification incomplete: '+str(exc)+'. Last successful checkpoint preserved.',file=sys.stderr)
        return 2


if __name__=='__main__':sys.exit(main())
