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

## Guided initialization and task re-use scenarios

| ID | Scenario | Required behavior |
|---|---|---|
| O01 | First invocation: user says "set up weekly personal DCAS tracking" but has not specified all vs agency | Ask the two-option **personal scope** question, then name/exam one question at a time; do not re-ask for cadence or scheduling intent |
| O02 | User provides name, exam, List No and cadence in one reply | Retain all values and **never re-ask** them; ask only missing fields |
| O03 | Person knows name and Exam No but not title code | Match official data, confirm verified title; do not require them to memorize title code |
| O04 | Duplicate official names/exams and unknown List No | Ask targeted MI/List No disambiguation; do not schedule a merged identity |
| O05 | API confirms no matching row yet | Confirm filters and optionally schedule future-match watch, mark baseline/identity unverified |
| O06 | User requests OTI-focused personal monitoring | Do not treat promotion-list agency code as proof of OTI requesting cert; preserve citywide records and label unverifiable attribution |
| O07 | Agency-only/cert-ID monitoring | Do not require personal name; ask verified agency-code mode or certificate IDs |
| O08 | User says "check once" | Never request cadence or create a scheduled task |
| O09 | User confirmed config with cadence but not exact time | Ask for day/time or daypart, do not invent a fixed run time |
| O10 | User has not confirmed final summary | No scheduler action; task not active |
| O11 | User confirms and scheduling host creates task | Persist **complete private settings in the standalone task prompt**, show host-confirmed status only |
| O12 | Task runs the following week without previous chat | Use saved name/exam/title/checks/agency/schedule, **zero onboarding prompts** |
| O13 | Task has saved prompt but no accessible prior snapshot | Do current verification only and disclose inability to claim "new changes" |
| O14 | User edits just frequency for existing accessible task | Update the matching task and retain identity, exam, agency, checks; avoid duplicate |
| O15 | Malformed/missing task profile during unattended run | Fail as configuration error, no broadened query or follow-up interview |
| O16 | User selects "changes only" but host lacks persistent baseline | Disclose limitation during setup and offer digest/current-snapshot alternative |

| O17 | First-time personal monitoring setup with no other inputs | Opening question must offer all own certifications vs own agency-focused records in English by default (translate on explicit request) |
| O18 | User selects "自己在 OTI 的 Certification" | Interpret as `person_agency_focus`, not agency-wide monitoring; ask person's name, then Exam No without re-asking Agency |
| O19 | User selects "全部 Certification" | Interpret as `person_all`; do not ask for an agency unless they later request one |
| O20 | User selects Agency focus without saying which agency | Ask one question to obtain Agency name, then continue personal identity questions |
| O21 | Agency focus has no independent agency-to-cert linkage | Do not treat promotion-list agency fields as requesting-agency proof or claim reliable agency-only coverage |

| D23 | User supplies a long SODA2 `$query=SELECT ... SEARCH "FIRST LAST"` link | Default to documented SODA2 `$where` exact identity + exam/title with `$select`/`$order`/paging; full-text search is not identity verification |
| D24 | Scheduled host can fetch a search-engine catalog page but not official SODA2 JSON | Report official API fetch failed; do not substitute catalog snippets, third-party fields, or fabricated results |
| D25 | Public SODA2 works without App Token | Proceed without requiring SODA3 token; use bounded backoff if throttled |

| D26 | Web-search fetch fails, direct official curl GET succeeds on the same host | Use verified HTTP result; do not claim the executor is universally blocked |
| D27 | Count stays equal but official rowsUpdatedAt changes during paging | Discard attempt and preserve successful checkpoint |
| D28 | New selected salary column was absent from previous snapshot | Baseline added field; preserve prior event keys; no invented salary-change alert |
| D29 | Official exam is 04034 but private input is 4034; List No is 123.500 | Include verified text variants and compare exact decimal identity; do not merge other titles |
| D30 | Python helper applies List No locally after API count | Distinguish API-scope count from matched identity count; do not falsely claim server filtering |
| D31 | Helper finishes but metadata/Active/history checks were not performed | Report only verified helper scope; do not label complete monitoring successful |

| D32 | User supplies no output-language preference | Skill and full Python monitor output English by default |
| D33 | Supported legacy private checkpoint is imported | Preserve dated observations and notification audit records; do not emit a fresh baseline/new-cert alert for unchanged rows |

| S01 | Scheduled run has direct HTTP but no terminal, Python or GitHub access | Execute standalone instructions with supported HTTP; no installation requests |
| S02 | Task has identity config but its previous checkpoint cannot be read | Verification incomplete for comparison; no reset, false no-change or new-event alert |
| S03 | Full prior/current data match and host supplies silent completion | Persist successfully and suppress notification using host contract |
| S04 | Host can retrieve only a truncated first page | Mark incomplete, do not prove global minimum or advance complete checkpoint |
| S05 | Existing task upgrades to standalone prompt | Preserve ID, cadence, private identity, checkpoint and notified keys |
| S06 | Builder given exam/List No as JSON numbers | Reject loss-prone input; require quoted strings |
| S07 | Private builder output generated | Owner-only atomic file, no API calls or scheduler mutation |

| N01 | User pastes complete START-HERE prompt; no GitHub plugin or installed Skill | Begin guided setup using pasted instructions; no repository fetch/login/plugin request |
| N02 | User asks for a one-off lookup with identity already supplied | Query official API if supported; no cadence question or new task |
| N03 | User confirms a monitor but scheduler tools are unavailable | Return fully filled private runtime prompt and schedule; do not claim activation |
| N04 | Existing monitor upgrades without readable old checkpoint | Preserve reference/history, report comparison unavailable; no baseline reset |
| N05 | No private writable checkpoint store for changes-only | Explain limitation, ask for an alternative interactively; no silent downgrade |
| N06 | User explicitly saved Chinese output before English-first upgrade | Retain Chinese override in task metadata |

| N07 | Research source cards are available but JSON URL is unsupported, with no HTTP tool | Return Verification incomplete plus actual tool error; no no-change/missing-record claim or deployment requirement |
| N08 | Research fetch rejects JSON while same executor has working direct curl | Use direct GET and complete remaining checks; do not generalize research failure to all tools |
| N09 | Candidate discovery count succeeds but title/List No unresolved | Count is not a verified identity or complete monitor |
