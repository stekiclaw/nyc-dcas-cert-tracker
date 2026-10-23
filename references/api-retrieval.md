# Reliable DCAS API Retrieval / NYC DCAS 数据稳定获取

## Direct SODA2 endpoint first

- Certifications: https://data.cityofnewyork.us/resource/a9md-ynri.json
- Active lists: https://data.cityofnewyork.us/resource/vx8i-nprf.json
- Metadata and schema check: https://data.cityofnewyork.us/api/views/a9md-ynri.json (change ID for active lists)

**Default strategy:** use public **SODA2.1** `GET /resource/a9md-ynri.json` with `$select`, `$where`, `$order`, `$limit` and `$offset`. These clause parameters are the documented straightforward way to reproduce an exported long `$query=SELECT ... SEARCH "NAME"` URL. For a scheduled personal monitor, avoid full-text `SEARCH` as the identity matcher; prefer verified first/last name and exam/title, then List No if needed. SODA3 is **not** the default and may require an App Token. An app token is optional for ordinary public SODA2 reads but can improve rate limits. If the official endpoint cannot be accessed, the correct outcome is `verification incomplete`, not a substitute source or empty candidate list.

Example selecting the requested certification columns (illustrative fictional person):

```bash
curl --fail-with-body --show-error --silent --get \
  'https://data.cityofnewyork.us/resource/a9md-ynri.json' \
  --data-urlencode '$select=exam_no,list_no,first_name,mi,last_name,list_agency_code,list_agency_desc,list_title_desc,cert_seq_no,request_date,salary,cert_issue_no,cert_date,reissue_date,cert_expiration_date,no_certified,no_requested,provisional_replacement,no_vacancies,list_title_code,sel_cert_description' \
  --data-urlencode "\$where=first_name='ALEX' AND last_name='EXAMPLE' AND exam_no in('04034','4034') AND list_title_code='13621' AND list_no=123.500" \
  --data-urlencode '$order=cert_date DESC, cert_issue_no DESC, cert_seq_no ASC, :id DESC' \
  --data-urlencode '$limit=1000' \
  --data-urlencode '$offset=0'
```

**Never run the Socrata catalog search on every query.** These dataset IDs are known. Catalog discovery is only for a genuinely unknown or changed dataset identifier. Read the data directly using SODA2.1 GET and URL-encoded `$where`, `$order`, `$limit`, and `$offset`. A browser-based agent may issue these direct URLs; a terminal can use the following curl commands.

```bash
curl --fail-with-body --silent --show-error --location \
  --retry 5 --retry-delay 2 --connect-timeout 10 --max-time 60 \
  --get 'https://data.cityofnewyork.us/resource/a9md-ynri.json' \
  --data-urlencode "\$where=exam_no='4034' AND last_name='EXAMPLE'" \
  --data-urlencode '$order=request_date DESC, :id DESC' \
  --data-urlencode '$limit=1000' --data-urlencode '$offset=0'

# Query the same scope's count, both before and after paging:
curl --fail-with-body --silent --show-error --get \
  'https://data.cityofnewyork.us/resource/a9md-ynri.json' \
  --data-urlencode '$select=count(*) as total' \
  --data-urlencode "\$where=exam_no='4034' AND last_name='EXAMPLE'"

# Inspect official schema if a query fails with HTTP 400:
curl --fail-with-body --silent --show-error \
  'https://data.cityofnewyork.us/api/views/a9md-ynri.json' | \
  jq '{rowsUpdatedAt,fields:[.columns[].fieldName]}'
```

The examples are synthetic and contain no real candidate information. Keep identifiers such as `exam_no` and `list_title_code` as text, retaining leading zeros. Escape apostrophes within SoQL string literals by doubling them (e.g. `O''NEILL`). Distinguish numerical `list_no` from text IDs. Never put a SODA app token into a public URL; supply `SODA_APP_TOKEN` in an environment variable and send it using the `X-App-Token` header.

## Completeness and error policy

1. Filter narrowly by the **valid fields in that dataset** before paging; never try to download the 6M+ rows by default. Do not mistakenly filter by `list_agency_code` when computing a candidate-wide global minimum.
2. Use a deterministic total order (`cert_date DESC, cert_issue_no DESC, cert_seq_no ASC, :id DESC` for certifications; `list_no ASC, :id DESC` for active lists after validating that dataset schema). Default to 1,000 rows per page. Explicitly page with `$limit` and `$offset`; the default page is incomplete.
3. Verify HTTP 2xx and JSON array response for each page, expected page lengths, aggregate count, and another `count(*)` after retrieval. Read official metadata before and after paging and require unchanged `rowsUpdatedAt`, in addition to equal counts and expected page lengths. When the dataset changes during paging, **discard that attempt**. An unchanged count reduces but cannot entirely eliminate pagination race conditions.
4. Retry only transient errors (e.g. network timeouts, 408, 429, 500/502/503/504), using bounded retry delays and `Retry-After` when supported. Invalid 400 SoQL should trigger field-metadata validation, not blind retries. Auth errors 401/403 are not empty results.
5. `200 []` with a separately verified count of zero is a valid empty result. Failed requests, malformed JSON, partial pages, schema mismatch, or missing evidence are **unknown/incomplete**, not 'no change'. Preserve the latest verified snapshot.
6. Report observation date in America/New_York, dataset `rowsUpdatedAt` separately from row-level `request_date`, `cert_date`, `reissue_date`, and `cert_expiration_date`. Updates to the dataset timestamp alone are not certification events.

### Optional terminal helper

```bash
bash scripts/fetch-soda.sh --dataset a9md-ynri \
  --where "exam_no='4034' AND last_name='EXAMPLE'" \
  --page-size 1000 --out certifications.json

# Optional application token (never commit the real value):
# export SODA_APP_TOKEN='YOUR_APP_TOKEN'

# Offline tests (Python needed for tests only):
python3 -m unittest discover -s tests -v
```

The helper needs bash, curl, jq, but the Skill remains prompt-only and does **not** depend on this helper. It rejects unfiltered requests, caps rows at 50,000 by default, retries bounded transient failures, verifies pagination and pre/post counts, and updates the output file only on a complete result.

## Critical agency attribution limitation

NYC's certification dataset defines `list_agency_code` / `list_agency_desc` as **promotion list** attributes; the values do **not** reliably prove which appointing agency requested a certificate. The certification dataset alone may therefore be insufficient to label an open-competitive certificate as OTI/DCWP/SBS. Without independent official linkage, present certificate number and candidate sequence with **requesting agency unverified**. `cert_issue_no` is not proof of a hire or permanent appointment.

## SODA3 note

SODA3 uses `/api/v3/views/{id}/query.json`, a full SoQL `query` or JSON POST payload, and an application token or authenticated identity. Do not send SODA2 fragment parameters to it or assume identical response shape. SODA2.1 remains a supported direct path.

Official references: [NYC certification data](https://data.cityofnewyork.us/d/a9md-ynri), [Socrata paging](https://dev.socrata.com/docs/paging.html), [App tokens](https://dev.socrata.com/docs/app-tokens), [SODA3 usage](https://support.socrata.com/hc/en-us/articles/43491231777047-Using-the-SODA3-API).


## Network/DNS failure triage and proven alternate runner

Before changing SoQL syntax, isolate failures **at the transport layer**:

| Symptom | Meaning | Next step |
|---|---|---|
| `curl: (6) Could not resolve host` / Python `gaierror` | DNS failure **before** an HTTP request exists | Test a control hostname (such as `example.com`), then the official domain; inspect runtime DNS/egress policy |
| All unrelated public hostnames fail and direct public IP HTTPS also fails | Container/sandbox-wide DNS/outbound restriction is likely | Switch the API fetch to a **supported egress-enabled executor**, or request platform network access; API parameters and tokens cannot repair this |
| DNS succeeds, TCP 443 fails | HTTPS egress/firewall/proxy issue | Configure approved HTTPS egress and proxy on the **actual runner**, never hard-code an IP or disable TLS certificate checks |
| HTTP 400 | Query or schema problem | Validate SODA2 SoQL fields using official metadata |
| HTTP 401/403 or 429 | Authorization or throttling | Verify supported authentication, token/rate limits and backoff |
| HTTP 200 but malformed/short JSON | Invalid/incomplete result | Reject the observation, preserve last verified baseline |

Run this **public, privacy-safe diagnostic** on the host that actually performs the scheduled query:

```bash
python3 scripts/check_api_network.py
```

This probes the official SODA2 endpoint using only `$select=exam_no&$limit=1`; it never queries a candidate, outputs their name, or embeds an API token. Exit status `0` means the official JSON API was successfully reached, `2` means DNS resolution failed, and `3` means HTTP/TLS/JSON failed. A control hostname is checked only when the official DNS lookup fails.

A separate optional GitHub Actions workflow `.github/workflows/soda2-connectivity.yml` performs the same diagnostic on a GitHub-hosted Ubuntu runner. **On 2026-10-23** a GitHub Actions run passed with "DNS OK" and "SODA2 OK: HTTP 200, JSON array". This is evidence that the official API could be reached from that GitHub runner, **not** a guarantee that a ChatGPT scheduled-task host has the same networking.

**Repair boundary:** this repository cannot change DNS or outbound firewall policy for ChatGPT-hosted tasks. If the task host lacks network access, it must run the fetch in an allowed executor (e.g. a suitably configured private Ubuntu server or a GitHub Actions workflow with appropriate private handling of candidate filters and checkpoint data). A publicly hosted GitHub workflow should **never put personal monitoring settings or resulting person-specific records into public job logs, workflow artifacts or commits**. Do not silently migrate to public storage. A connectivity-only GitHub Action does **not** itself run personal monitoring.


## Python implementation (preferred when a private execution host has HTTPS egress)

```bash
python3 scripts/fetch_certifications.py \
  --first-name ALEX --last-name EXAMPLE \
  --exam 4034 --title-code 13621 --list-no 103.000 \
  --out /private/path/certifications.json

python3 -m unittest discover -s tests -p test_fetch_certifications.py -v
```

The example is entirely synthetic. The Python stdlib implementation builds official SODA2 `$where`, `$select`, `$order`, `$limit` and `$offset` requests; validates identities and count consistency; handles 4034/04034 as exam-text variants and List No using `Decimal`; retries transient network failures; and writes a 0600 private JSON only after a complete fetch. It does not require curl, jq, requests or an App Token for public queries. The output contains personal data, and must **never** be stored in a public GitHub repository, Actions logs or artifacts.

A GitHub-hosted Actions smoke test exercises this Python script with a **fictional unmatched name**. It verifies that real filtered SODA2 GETs work over the public network, but does not fetch, store or expose a real candidate's record; doing that in production requires a private execution and data-storage arrangement. Network access is specific to the actual executor and tool. Do not describe every ChatGPT container as blocked based on a different execution environment's failure. Direct HTTP success and a web-search fetch failure can coexist.

## Helper boundary and checkpoint compatibility

The optional Python helper currently performs List No filtering locally using Decimal after complete name/exam/title retrieval. Preserve `count_before_list_filter` versus `matched_count`; do not claim its API count included List No. A host that adds List No to a direct SODA2 `$where` must use that exact same clause for both counts. The helper does not itself implement metadata stability checks, Active List queries, global minima, month/year analysis or durable event comparison: complete those host-level steps before declaring a full monitor run successful.

Preserve the original exam text and observed equivalent leading-zero variants in rows. Use numeric Decimal comparison only for numeric fields such as List No and Cert Seq No. When adding newly selected fields, compare common fields to the previous successful snapshot and establish an observation baseline for added fields; do not manufacture a change from previously unobserved values. Keep notified event keys across transport/schema upgrades.

For private monitoring, store full identity filters, selected fields, exact API predicate, paging/count evidence, source update times, observation time, and independently verified agency attribution links. Keep the requesting agency unverified if no official association exists; group by certificate without using promotion-list codes to filter global results.
