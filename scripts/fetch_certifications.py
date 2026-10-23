#!/usr/bin/env python3
"""Fetch candidate-specific NYC DCAS certification rows via public SODA2 (Python stdlib).

Keep --out private: JSON includes candidate identity and all matched records.
Never publish the result to a GitHub commit, Actions log or public artifact.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://data.cityofnewyork.us/resource/a9md-ynri.json"
FIELDS = (
    "exam_no,list_no,first_name,mi,last_name,list_agency_code,list_agency_desc,"
    "list_title_desc,cert_seq_no,request_date,salary,cert_issue_no,cert_date,"
    "reissue_date,cert_expiration_date,no_certified,no_requested,"
    "provisional_replacement,no_vacancies,list_title_code,sel_cert_description"
)
RETRYABLE = {408, 429, 500, 502, 503, 504}


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def exam_forms(exam):
    """Preserve exam identifiers as text and accept 4034 / 04034."""
    exam = str(exam).strip()
    if not exam.isdigit():
        raise ValueError("Exam No must be numeric text")
    stripped = exam.lstrip("0") or "0"
    return sorted({exam, stripped, stripped.zfill(5)})


def build_where(first, last, exam, title=None):
    name = [first.strip().upper(), last.strip().upper()]
    if any(not v for v in name):
        raise ValueError("First and last names are mandatory")
    clauses = [f"first_name={literal(name[0])}", f"last_name={literal(name[1])}"]
    clauses.append("(" + " OR ".join(
        f"exam_no={literal(v)}" for v in exam_forms(exam)) + ")")
    if title:
        clauses.append(f"list_title_code={literal(title.strip())}")
    return " AND ".join(clauses)


def request_json(params, *, timeout=25, retries=4,
                 opener=urlopen, sleeper=time.sleep):
    url = BASE + "?" + urlencode(params)
    headers = {"Accept": "application/json",
               "User-Agent": "nyc-dcas-cert-tracker-python/1.0"}
    token = os.environ.get("SODA_APP_TOKEN", "").strip()
    if token:
        headers["X-App-Token"] = token
    for attempt in range(retries + 1):
        try:
            with opener(Request(url, headers=headers), timeout=timeout) as res:
                if res.status != 200:
                    raise ValueError(f"Unexpected HTTP status {res.status}")
                raw = res.read(16_000_001)
            if len(raw) > 16_000_000:
                raise ValueError("Response exceeded 16 MB limit")
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                raise ValueError("Expected a JSON array")
            return parsed
        except HTTPError as exc:
            if exc.code not in RETRYABLE or attempt >= retries:
                raise RuntimeError(f"Official SODA2 HTTP error {exc.code}") from exc
            retry_after = exc.headers.get("Retry-After", "")
            delay = (min(int(retry_after), 30)
                     if retry_after.isdecimal() else min(2 ** attempt, 15))
        except (URLError, TimeoutError, OSError) as exc:
            if attempt >= retries:
                raise RuntimeError(f"Official SODA2 transport failure: {exc}") from exc
            delay = min(2 ** attempt, 15)
        sleeper(delay)
    raise AssertionError("unreachable")


def get_count(where, requester=request_json):
    payload = requester({"$select": "count(*) as total", "$where": where})
    if len(payload) != 1 or not isinstance(payload[0], dict):
        raise ValueError("Malformed count response")
    value = payload[0].get("total")
    if value is None or not str(value).isdigit():
        raise ValueError("Invalid count total")
    return int(value)


def decimal_equal(a, b):
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except InvalidOperation:
        return False


def fetch(first, last, exam, title=None, list_no=None, page_size=1000,
          max_rows=50000, requester=request_json):
    where = build_where(first, last, exam, title)
    before = get_count(where, requester=requester)
    if before > max_rows:
        raise ValueError(f"Too many rows ({before}); narrow query")
    rows = []
    forms = set(exam_forms(exam))
    for offset in range(0, before, page_size):
        batch = requester({
            "$select": FIELDS, "$where": where,
            "$order": "cert_date DESC, cert_issue_no DESC, cert_seq_no ASC, :id DESC",
            "$limit": str(page_size), "$offset": str(offset)
        })
        wanted = min(page_size, before - offset)
        if len(batch) != wanted:
            raise ValueError(f"Incomplete page offset={offset}: {len(batch)} != {wanted}")
        for row in batch:
            if not isinstance(row, dict):
                raise ValueError("Invalid candidate row")
            if row.get("first_name", "").upper() != first.strip().upper():
                raise ValueError("Unexpected first_name in filtered response")
            if row.get("last_name", "").upper() != last.strip().upper():
                raise ValueError("Unexpected last_name in filtered response")
            if str(row.get("exam_no")) not in forms:
                raise ValueError("Unexpected exam_no in filtered response")
            if title and str(row.get("list_title_code")) != title.strip():
                raise ValueError("Unexpected title code in filtered response")
        rows.extend(batch)
    after = get_count(where, requester=requester)
    if before != after or len(rows) != before:
        raise ValueError(f"Dataset changed during paging/count drift: {before} -> {after}")
    if list_no is not None:
        rows = [row for row in rows if decimal_equal(row.get("list_no"), list_no)]
    return {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": BASE,
        "scope": {"first_name": first.upper(), "last_name": last.upper(),
                  "exam_no": exam, "title_code": title, "list_no": list_no},
        "count_before_list_filter": before,
        "matched_count": len(rows), "rows": rows
    }


def private_write(path, data):
    dest = Path(path).expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".dcas-", suffix=".tmp", dir=str(dest.parent))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(tmp, dest)
        os.chmod(dest, 0o600)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--exam", required=True)
    parser.add_argument("--title-code")
    parser.add_argument("--list-no")
    parser.add_argument("--out", required=True, help="PRIVATE JSON file path")
    parser.add_argument("--page-size", type=int, default=1000)
    parser.add_argument("--max-rows", type=int, default=50000)
    args = parser.parse_args()
    if not 1 <= args.page_size <= 5000 or not 1 <= args.max_rows <= 1000000:
        parser.error("page-size or max-rows out of range")
    try:
        data = fetch(args.first_name, args.last_name, args.exam,
                     args.title_code, args.list_no, args.page_size, args.max_rows)
        private_write(args.out, data)
        print("SODA2 verified: %s matching rows; saved to private JSON file."
              % data["matched_count"])
    except Exception as exc:
        print(f"SODA2 retrieval failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
