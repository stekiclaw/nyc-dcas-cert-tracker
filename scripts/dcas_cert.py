#!/usr/bin/env python3
"""Official DCAS queries. Output JSON; do not infer hiring or eligibility."""
import argparse
import calendar
import datetime as dt
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

DATASETS = {'active': 'vx8i-nprf', 'certifications': 'a9md-ynri'}
CERT_FIELDS = 'exam_no,list_title_code,list_no,list_agency_code,list_agency_desc,cert_issue_no,cert_seq_no,request_date,cert_date,reissue_date,cert_expiration_date,no_certified,no_requested,no_vacancies,provisional_replacement,sel_cert_description'
ACTIVE_FIELDS = 'exam_no,list_title_code,list_no,adj_fa,group_no,established_date,anniversary_date,extension_date'
NAME_FIELDS = ',first_name,mi,last_name'


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def number(value):
    try:
        n = Decimal(str(value))
        return n if n.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def date(value):
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def shift(d, months=0, years=0):
    idx = d.year * 12 + d.month - 1 - months - years * 12
    y, m = divmod(idx, 12)
    return dt.date(y, m + 1, min(d.day, calendar.monthrange(y, m + 1)[1]))


def read_url(url):
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.load(response)


def fetch(dataset, where, fields):
    base = 'https://data.cityofnewyork.us/resource/' + dataset + '.json?'
    def query(params):
        return read_url(base + urllib.parse.urlencode(params))
    metadata = read_url('https://data.cityofnewyork.us/api/views/' + dataset + '.json')
    available = {c['fieldName'] for c in metadata['columns']}
    missing = set(fields.split(',')) - available
    if missing:
        raise ValueError('Official schema missing fields: ' + ','.join(sorted(missing)))
    count = int(query({'$where': where, '$select': 'count(*)'})[0]['count'])
    rows = []
    for offset in range(0, count, 5000):
        rows.extend(query({'$where': where, '$select': fields, '$limit': 5000,
                           '$offset': offset, '$order': ':id'}))
    count_after = int(query({'$where': where, '$select': 'count(*)'})[0]['count'])
    after = read_url('https://data.cityofnewyork.us/api/views/' + dataset + '.json')
    if len(rows) != count or count_after != count or after.get('rowsUpdatedAt') != metadata.get('rowsUpdatedAt'):
        raise ValueError('Dataset changed during retrieval or pagination incomplete; retry without overwriting state')
    return rows, {'url': 'https://data.cityofnewyork.us/d/' + dataset,
                  'rows_updated_at': dt.datetime.fromtimestamp(metadata['rowsUpdatedAt'], dt.timezone.utc).isoformat(),
                  'matching_row_count': count}


def key(row):
    return tuple(row.get(f, '') for f in ('exam_no', 'list_title_code', 'list_agency_code', 'cert_issue_no', 'sel_cert_description'))


def identity(row):
    return (row.get('first_name', '').strip().upper(), row.get('mi', '').strip().upper(),
            row.get('last_name', '').strip().upper(), str(number(row.get('list_no'))))


def sequence_sort(row):
    return (row.get('cert_date', ''), row.get('reissue_date', ''),
            number(row.get('cert_issue_no')) or Decimal(0), number(row.get('cert_seq_no')) or Decimal(0))


def unique(rows):
    return list({json.dumps(r, sort_keys=True): r for r in rows}.values())


def analyze_person(active, rows, args, as_of):
    def matches(r):
        return (r.get('first_name', '').strip().upper() == args.first.strip().upper()
                and r.get('last_name', '').strip().upper() == args.last.strip().upper()
                and (args.mi is None or r.get('mi', '').strip().upper() == args.mi.strip().upper())
                and (args.list_no is None or number(r.get('list_no')) == number(args.list_no)))
    active = [r for r in active if matches(r)]
    rows = unique([r for r in rows if matches(r)])
    ids = sorted({identity(r) for r in active + rows})
    if len(ids) > 1:
        return {'status': 'candidate_ambiguous', 'candidate_identities': ids}
    if not ids:
        return {'status': 'no_matching_candidate', 'candidate_identities': []}
    if args.agency_code:
        rows = [r for r in rows if r.get('list_agency_code') == args.agency_code]
    rows.sort(key=sequence_sort)
    current, unknown = [], []
    for r in rows:
        issued, expiry = date(r.get('cert_date')), date(r.get('cert_expiration_date'))
        if issued is None or issued > as_of:
            continue
        if expiry is None:
            unknown.append(r)
        elif expiry >= as_of:
            current.append(r)
    seqs = [number(r.get('cert_seq_no')) for r in current]
    valid = [n for n in seqs if n is not None]
    minimum = min(valid) if valid else None
    month, year = shift(as_of, months=1), shift(as_of, years=1)
    recent = [r for r in rows if date(r.get('cert_date')) and month <= date(r['cert_date']) <= as_of]
    reissued = [r for r in rows if date(r.get('cert_date')) and date(r['cert_date']) < month
                and date(r.get('reissue_date')) and month <= date(r['reissue_date']) <= as_of]
    history = {}
    for r in rows:
        issued = date(r.get('cert_date'))
        if issued and year <= issued <= as_of:
            history.setdefault(r.get('list_agency_code', ''), []).append(r)
    for code, records in history.items():
        prior = None
        prior_batch = None
        enriched = []
        for r in records:
            s = number(r.get('cert_seq_no'))
            batch = key(r)
            enriched.append(dict(r, difference_from_previous_batch=str(s - prior) if s is not None and prior is not None and batch != prior_batch else None))
            prior = s
            prior_batch = batch
        values = [number(r.get('cert_seq_no')) for r in records if number(r.get('cert_seq_no')) is not None]
        history[code] = {'rows': enriched, 'best_observed_sequence': str(min(values)) if values else None,
                         'worst_observed_sequence': str(max(values)) if values else None}
    return {'status': 'ok', 'candidate_identities': ids, 'active_candidate_found': bool(active),
            'agency_scope': args.agency_code or 'all', 'current_minimum_sequence': str(minimum) if minimum is not None else None,
            'current_minimum_ties': [r for r in current if minimum is not None and number(r.get('cert_seq_no')) == minimum],
            'current_rows': current, 'current_rows_missing_sequence': [r for r in current if number(r.get('cert_seq_no')) is None],
            'unknown_expiry_rows': unknown, 'recent_month_start': month.isoformat(), 'recent_month_rows': recent,
            'older_certificates_reissued_in_month': reissued, 'annual_start': year.isoformat(),
            'annual_by_agency': history, 'older_certificates_reissued_in_year': [r for r in rows if date(r.get('cert_date')) and date(r['cert_date']) < year and date(r.get('reissue_date')) and year <= date(r['reissue_date']) <= as_of], 'all_personal_rows': rows}


def snapshot(active, rows):
    grouped = {}
    for r in unique(rows):
        k = json.dumps(key(r))
        g = grouped.setdefault(k, {'key': list(key(r)), 'fields': {}, 'list_numbers': set(), 'sequence_pairs': set()})
        n = number(r.get('list_no'))
        if n is not None:
            g['list_numbers'].add(n)
        g['sequence_pairs'].add((str(n), str(number(r.get('cert_seq_no')))))
        for f in CERT_FIELDS.split(','):
            if f not in ('list_no', 'cert_seq_no'):
                g['fields'].setdefault(f, set()).add(r.get(f, ''))
    for g in grouped.values():
        g['fields'] = {f: sorted(v) for f, v in g['fields'].items()}
        g['list_numbers'] = [str(n) for n in sorted(g['list_numbers'])]
        g['sequence_pairs'] = [list(pair) for pair in sorted(g['sequence_pairs'])]
    observation = {'present': bool(active), 'candidate_row_count': len(active)}
    for f in ('established_date', 'anniversary_date', 'extension_date'):
        observation[f] = sorted({r.get(f, '') for r in active})
    return {'certificates': grouped, 'active_observation': observation}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['person', 'monitor'])
    p.add_argument('--exam', required=True)
    p.add_argument('--title-code', required=True)
    p.add_argument('--first'); p.add_argument('--last'); p.add_argument('--mi')
    p.add_argument('--list-no'); p.add_argument('--agency-code')
    p.add_argument('--as-of', default=dt.datetime.now(ZoneInfo('America/New_York')).date().isoformat())
    p.add_argument('--input'); p.add_argument('--previous'); p.add_argument('--output', required=True)
    args = p.parse_args()
    if args.mode == 'person' and (not args.first or not args.last):
        p.error('person mode requires --first and --last')
    if args.list_no is not None and number(args.list_no) is None:
        p.error('--list-no must be a finite number')
    if not args.exam.isdigit():
        p.error('--exam must be numeric')
    as_of = dt.date.fromisoformat(args.as_of)
    where = 'exam_no in(' + ','.join(literal(e) for e in sorted({str(int(args.exam)), str(int(args.exam)).zfill(5)})) + ') AND list_title_code=' + literal(args.title_code)
    if args.mode == 'person':
        # Broaden server search for whitespace; exact normalized matching occurs locally.
        where += ' AND upper(first_name) like ' + literal('%' + args.first.strip().upper() + '%') + ' AND upper(last_name) like ' + literal('%' + args.last.strip().upper() + '%')
    if args.input:
        raw = json.loads(Path(args.input).read_text())
        def scoped(rows):
            return [r for r in rows if str(r.get('exam_no', '')).lstrip('0') == str(int(args.exam)) and r.get('list_title_code') == args.title_code]
        active, rows = scoped(raw['active']), scoped(raw['certifications'])
        sources = raw.get('sources', {})
    else:
        active, am = fetch(DATASETS['active'], where, ACTIVE_FIELDS + (NAME_FIELDS if args.mode == 'person' else ''))
        rows, cm = fetch(DATASETS['certifications'], where, CERT_FIELDS + (NAME_FIELDS if args.mode == 'person' else ''))
        sources = {'active': am, 'certifications': cm}
    result = {'exam': str(int(args.exam)), 'title_code': args.title_code, 'as_of': str(as_of),
              'queried_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'source_mode': 'snapshot' if args.input else 'live', 'sources': sources, 'snapshot_captured_at': raw.get('queried_at', raw.get('captured_at')) if args.input else None}
    if args.mode == 'person':
        result.update(analyze_person(active, rows, args, as_of))
    else:
        result['snapshot'] = snapshot(active, rows)
        result['initial_baseline'] = not bool(args.previous)
        result['changes'] = []
        if args.previous:
            old = json.loads(Path(args.previous).read_text())
            if old['exam'] != result['exam'] or old['title_code'] != result['title_code']:
                raise ValueError('Previous snapshot scope differs')
            a, b = old['snapshot']['certificates'], result['snapshot']['certificates']
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    result['changes'].append({'key': json.loads(k), 'old': a.get(k), 'new': b.get(k)})
            if old['snapshot']['active_observation'] != result['snapshot']['active_observation']:
                result['changes'].append({'active_observation_old': old['snapshot']['active_observation'], 'active_observation_new': result['snapshot']['active_observation']})
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + '.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    temporary.replace(destination)
    print(json.dumps({'status': result.get('status', 'ok'), 'output': str(destination), 'changes': len(result.get('changes', []))}))


if __name__ == '__main__':
    main()
