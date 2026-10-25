# Official data and reporting

Use only NYC DCAS official pages/notices and DCAS-owned NYC Open Data. Direct SODA2.1 GET:

```text
https://data.cityofnewyork.us/resource/a9md-ynri.json
https://data.cityofnewyork.us/resource/vx8i-nprf.json
https://data.cityofnewyork.us/api/views/a9md-ynri.json
https://data.cityofnewyork.us/api/views/vx8i-nprf.json
```

The complete [runtime contract](scheduled-task-prompt.md) defines identity predicates, encoded GETs, page/count/timestamp checks and failure output. No external storage or scripts are required. Strip unsupported UTM/link-tracking parameters. A successful count probe establishes transport only; a source description or API failure establishes no candidate facts.

| Official field | Interpretation |
|---|---|
| exam_no / list_title_code | Both required for verified exam/title scope; preserve official text/leading zeros |
| first_name / mi / last_name / list_no | Verify exact identity; List No is an exact decimal, not Cert Seq |
| list_agency_code / list_agency_desc | Promotion-list attributes; requesting agency needs independent official evidence |
| cert_issue_no | Batch identity within exam/title; keep raw agency/selection variants within it |
| cert_seq_no | Personal sequence within this cert, not global rank, hiring or appointment order |
| request_date / cert_date | Request versus issue date; “cert created” should identify which date |
| reissue_date / cert_expiration_date | Reissue versus dated expiry; expiry-today included, missing expiry unknown |
| no_certified / no_requested / no_vacancies | Published counts, not actual hires; distinguish rows and distinct candidates |
| sel_cert_description / provisional_replacement | Conditions/flag, never permanent appointment evidence |
| established_date / anniversary_date / extension_date | Verify Active's own schema; anniversary alone is not independent confirmed termination |
| adj_fa / group_no | Published score/group, not automatically a tie-breaking group |

Use New York dates by default. Calendar-month/year subtraction clamps invalid month-end dates; include both endpoints and exclude future issues. Flag older certs reissued in the window separately. Preserve every tied minimum and same-day batch. Do not infer continuous coverage between min/max List No.

One-year visible batches: chronological cert numbers, dates, personal seq, published count, selection, expiry, known official requesting agency. Compare first/latest/best/worst visible values with gaps. Differences across certs are not changes within a cert; do not attribute them to hires/removals.

For earlier observation comparisons, use actually accessible successful dated ChatGPT results only. Record event date, source-wide rowsUpdatedAt and current observation date separately. Compare verified common fields; added fields have no old value. A partial old table cannot prove new inclusion or full coverage. No accessible prior results means comparison unknown. Ordinary evidence tables in task output are allowed, but no external checkpoint, hidden state, prompt mutation or durable notification log is required or created.

Keep facts separate from clearly marked implications for same-score candidates. Certification, range, seq, published counts and provisional replacement cannot prove reachability, actual employment, Permanent Appointment or every tied person's selection. Missing records alone prove none of these. Independently confirm list termination/extension from official notices.
