---
name: nyc-dcas-cert-tracker
description: Prompt-only workflow for official NYC DCAS certification and active-list research, personal Cert Seq No comparisons, and cloud-agent scheduled change monitoring. No Python, database or local service required.
---

# NYC DCAS Cert Tracker

## Contract and execution modes
This is a **prompt-only, host-operated Skill**. The web/agent host supplies web browsing, reasoning, memory or previous runs when supported, scheduling and notifications. Never assume a background service, local script, permanent storage, or that scheduling automatically invokes this file.

- **Interactive:** Offer functions (multiple may be selected): (1) lowest current personal Cert Seq No among **all** agencies and all ties; (2) named-agency batches and personal sequences; (3) all personal batches in the past calendar month; (4) one-year agency history; (5) material-change monitoring.
- **One scheduled run:** Use saved parameters from the task. Execute the selected functions now, compare against the latest *successfully verified* previous observation if it is accessible, and return only meaningful changes when configured to alert-only. Do not ask setup questions inside a background run.
- **Task setup:** Only upon a user's scheduling request, help create separate named recurring tasks (per exam/title and selected agencies/functions). Use the host's supported scheduling action. If unavailable, provide a self-contained task prompt from [task-templates.md](references/task-templates.md) for manual setup. Reuse an existing equivalent task when able; avoid duplicates. Scheduling must not depend on the agent possessing this file later. Do not say a task was scheduled unless the host confirms it.

Respond in the user's language. Keep personal names/list numbers out of the public repository.

## Inputs and identity
For personal conclusions, obtain First Name, Last Name, optional MI, exam number, title or title code, and preferably exact List No; agency selection only for agency-specific work. Never ask for SSN, DOB, home address or employee ID. Accept supplied values in task private instructions or supported private host state. In background runs, missing or conflicting essential identity means report configuration/identity uncertainty rather than guessing.

Use exact normalized official name, MI and List No. For ambiguous identities do not merge results: require user selection at next interaction. Normalize case/whitespace, not fuzzy matches. Scope *both* exam and title code (e.g. CA Operations 4034/04034 with 13621); check reused exam numbers.

## Reliable data acquisition (required)
Prefer direct official SODA2.1 GET requests to https://data.cityofnewyork.us/resource/a9md-ynri.json (certifications) and https://data.cityofnewyork.us/resource/vx8i-nprf.json (active lists). Do not run a Socrata catalog search at the start of every query; IDs are fixed. A browser/HTTP host may read encoded URLs directly. With terminal access, use curl --get --data-urlencode for SoQL `$where`, `$order`, `$limit`, `$offset`; optional `scripts/fetch-soda.sh` verifies counts and paginates.
Filter to the requested exact candidate/exam scope before paging. Check count(*) before/after; use a deterministic total order (request_date DESC, :id DESC for certifications, :id DESC for active lists). Validate status, JSON array, each page's length and aggregate count. Do not treat 4xx, 429, timeout, malformed JSON or incomplete pagination as empty or unchanged data. Retry transient 408/429/5xx with bounds and delays; on 400 check the official /api/views/{id}.json schema, not an unrelated dataset. SODA3 requires a different complete-query syntax and app token; it is not a transparent `$where` fallback. See [retrieval guide](references/api-retrieval.md).
**Agency attribution:** In certification records, `list_agency_code` and `list_agency_desc` are promotion-list attributes, NOT necessarily the appointing agency that requested a certification. Never infer OTI/DCWP/SBS or another recruiting agency from them alone. When independent official attribution is unavailable, show cert number with appointing agency unverified. Do not restrict a global candidate search to promotion-list agency codes.
## Official-source research and computation
Read [data-and-reporting.md](references/data-and-reporting.md). Use NYC DCAS / DCAS-owned Open Data as facts:
- Certifications https://data.cityofnewyork.us/d/a9md-ynri (API `a9md-ynri`)
- Active lists https://data.cityofnewyork.us/d/vx8i-nprf (API `vx8i-nprf`)
- Relevant official DCAS notices for independently verified expiry/termination.

When tools allow, inspect official field names, retrieve every matching page (not a default 1,000-row subset), verify count/completeness and dataset update time. Where tool limits prevent full retrieval, explicitly label results partial and never claim a **global** minimum. Record New York as-of date, source timestamps, official links and issuance dates separately. A failed query/schema mismatch is **unknown**, not "no change."

Cert batch key = (exam_no, list_title_code, cert_issue_no); a promotion-list agency code is auxiliary and not the recruiting agency. `sel_cert_description` is a condition within the batch, not an extra batch. A request date can have multiple cert numbers. Preserve exact decimal List No and numeric Cert Seq No. Cert Seq No is *within that cert*, not global ranking, reachability, a hire or permanent appointment. Keep distinct list numbers and published `no_certified` separate.

Current dated observations: certification issued by as-of, expiration >= as-of (including today); missing expiry = unknown, excluded from confirmed-date minimum. For *global* minimum, fetch all agencies and include all tied cert rows, not merely each agency's best. Use calendar month/year windows ending as-of inclusive; note reissues of older certs separately. For agency history compare first/latest/best/worst *observed* rows, preserve same-day batches and gaps; changes across cert numbers are NOT movements inside a single cert. Never infer hires, list removal, appointment or tie-breaking from sequences, list ranges, `group_no`, `provisional_replacement` or missing certs.

## State, baseline, and notification rules
Use only host-confirmed persisted task instructions / monitoring memory / prior-run results if accessible. Before comparing, confirm identity scope, source, cert key, and baseline date. Prefer a compact per-task checkpoint containing:
`task_scope; as_of; sources_updated_at; status; personal_rows:[agency,cert_issue_no,seq,list_no,cert_date,reissue_date,expiry,selection]; cert_batches:[agency,cert_issue_no,distinct_list_numbers,published_count,expiry]; last_notified_event_keys`.
Keep checkpoint private. Do not assume previous runs are accessible or persisted; if absent, this run is a **baseline** and must not invent deltas. No historical backfill from memory unless supported by verifiable dated evidence.

Material, evidence-backed notifications:
1. New certification/agency including the candidate.
2. Changed personal sequence or inclusion in the **same** certificate in two verified dated observations.
3. Changed published coverage, selection criteria, reissue or expiry on a known certificate.
4. Independently verified official list termination/extension.

Suppress repeat event keys and mere source-wide update timestamps, unchanged rows, calendar expiry passage alone, and first-baseline "change alerts". A missing record alone requires confirmation; flag as *unverified disappearance*, not removed/hired. If data fails, preserve last successful checkpoint and surface a concise monitoring error according to host policy, never "no change." If the host cannot retain state, report only an as-of snapshot and clearly say cross-run alerts are not reliable.

On alert: agency, cert number, request/issue/reissue dates, old/new sequence or published values, expiry, source link and observation dates. On no material change, suppress notification if the host supports silent/conditional monitoring; otherwise give the shortest factual no-change result. Avoid large repeated baseline tables in notifications.

## Portable setup and evaluation
Task prompts must be standalone for ChatGPT Scheduled or another browser agent that cannot auto-load Skills. See [task-templates.md](references/task-templates.md); do not rely on "read GitHub SKILL.md" as the only instruction. Use [acceptance-scenarios.md](references/acceptance-scenarios.md) to check agent behavior after changes; these are prompt-based evaluation scenarios, not executable tests.
