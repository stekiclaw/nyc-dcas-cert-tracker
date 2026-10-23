# DCAS Prompt-Skill Acceptance Scenarios

Manually run these against a capable browser/agent host using official data or explicitly labeled synthetic records. Record the observed answer and sources. Passing a text checklist is not a guarantee of actual scheduled execution.

| ID | Scenario | Required behavior |
|---|---|---|
| D01 | Candidate has cert sequences 4 (Agency A), 4 (Agency B) and 9 (Agency C) | Global minimum = 4, show A+B and every tied cert; cannot apply Agency-only filter |
| D02 | Same agency/exam/title/cert_no with two selection descriptions | One certificate batch, retain both descriptions |
| D03 | Two people share name but differ in MI / List No | Pause personal conclusion until identity disambiguated |
| D04 | Cert expired yesterday / expires today / missing expiry | Exclude yesterday; include today; unknown expiry separate |
| D05 | Two different cert numbers have sequences 8 and 3 | Difference is between batches, not proof someone was hired |
| D06 | Older cert was reissued during the past month | Separately flag reissue; do not treat as new issue date |
| D07 | Dataset default page omits later personal rows | Paginate; if incomplete, explicitly state no global minimum proved |
| D08 | First scheduled run has no verified previous checkpoint | Baseline, not a change alert |
| D09 | Dataset update timestamp changes with identical rows | No material-change notification |
| D10 | Same cert personal sequence 8 to 6 on two reliable dates | Material event, include old/new dates and cert number, without hiring inference |
| D11 | Cert disappears from one source response | Unverified, reconfirm; do not claim list removal |
| D12 | API failure / schema mismatch | Preserve last good observation, label unknown; never say "no change" |
| D13 | Monitoring host cannot retain prior runs or suppress alerts | Disclose limitation; do current snapshot; don't claim durable comparison |
| D14 | User only asks for current status | No scheduled task created |
| D15 | Task instructions are copied into a host without Skill loading | Standalone prompt still includes all critical source, grouping, filtering and notification rules |

Use New York date, official links, source update timestamps and fact-vs-inference distinctions for every case.

| D16 | Fixed dataset ID already known | Query known SODA2.1 endpoint directly; no catalog search on ordinary run |
| D17 | 429/503 followed by success | Bounded retry, then verified JSON; never call it empty on HTTP error |
| D18 | Pages fetched but count changes from beginning to end | Reject result, preserve last verified snapshot |
| D19 | Active list query ordered by nonexistent request_date | Choose valid order (:id DESC) instead of importing certification schema |
| D20 | Open-competitive certification has promotion list agency code 000 | Do not assert a requesting agency without separate official linkage |
| D21 | HTTP 200 returns JSON object instead of array | Reject malformed API result, not a verified zero |
| D22 | HTTP 400 unknown SoQL field | Inspect /api/views/{id}.json field names; no unbounded retry |
