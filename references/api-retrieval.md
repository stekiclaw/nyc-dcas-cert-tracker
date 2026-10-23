# Reliable DCAS API Retrieval / NYC DCAS 数据稳定获取

## Direct SODA2 endpoint first

- Certifications: https://data.cityofnewyork.us/resource/a9md-ynri.json
- Active lists: https://data.cityofnewyork.us/resource/vx8i-nprf.json
- Metadata and schema check: https://data.cityofnewyork.us/api/views/a9md-ynri.json (change ID for active lists)

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
2. Use a deterministic total order (`request_date DESC, :id DESC` for certifications; `:id DESC` for active lists). Explicitly page with `$limit` and `$offset`; the default page is incomplete.
3. Verify HTTP 2xx and JSON array response for each page, expected page lengths, aggregate count, and another `count(*)` after retrieval. When the dataset changes during paging, **discard that attempt**. An unchanged count reduces but cannot entirely eliminate pagination race conditions.
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
