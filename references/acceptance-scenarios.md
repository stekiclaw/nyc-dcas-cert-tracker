# Prompt-only acceptance scenarios

Version 2026-10-26.2. Evaluate with the complete START-HERE prompt and labeled synthetic inputs when live tools are unavailable. These are manual behavioral checks, not executable tests or proof of real Scheduled Tasks compatibility.

| Scenario | Required behavior |
|---|---|
| First-time user without GitHub, Python, external storage | Ask one missing setup question; no external tool/service/storage requirement |
| Identity and one-off query already supplied | Reuse inputs, query now if supported; no scheduling questions/task creation |
| Current_snapshot, complete data, no prior outputs | Report selected current results; no new-event claim |
| Verified_changes, prior run inaccessible | Comparison unavailable; no external checkpoint request, no no-change claim |
| Prior matching complete set contains X, current has X+Y | Can report verified new Y with old/new dates and evidence |
| Prior result only shows minimum X, current also has Y | Cannot infer Y is newly certified from an incomplete old list |
| Same cert seq8 then6 in two dated results | Within-cert observed change, no hiring inference |
| Distinct certs seq8 and6 visible today | Cross-batch difference only, no within-cert history claim |
| Earlier year of snapshots absent | Report currently visible year only, no reconstructed snapshot history |
| Minimum4 appears in two agencies/multiple certs | Include every tie; preserve unknown agency attribution |
| Missing expiry/seq among eligible rows | Unknown expiry separately; missing seq prevents proved global minimum |
| Promotion-list agency code matches focus agency | Still require independent requesting-agency evidence |
| DisabledError with no HTTP status and no direct alternative | Verification incomplete with actual error, no invented403/DNS or deployment detour |
| Copied API URL includes utm_source and identity filters | Strip tracking key, retain identity, retry corrected400 once |
| Moving timestamp/count or truncated pagination | Affected check incomplete; no global minimum/comparison success |
| Coverage requested with earlier exact sets accessible | Fetch exact relevant batches, complete checks, compare sets; no unnecessary whole-exam fetch |
| Already-reported transition visible in prior outputs | Suppress repeat if identity/transition/date evidence matches |
| Notification history not accessible | Deduplication unknown, no exactly-once promise |
| Task setup after failed direct preflight | Do not claim/create a verified working monitor |
| Authorized upgrade of existing task | Retain ID/schedule/identity/language, remove external-state dependency; leave external data untouched |
| Installed Skill references | All retained local links resolve; no scripts/deployment/storage prerequisite |
| Normal chat succeeds, scheduled run not tested | Disclose actual scheduled compatibility remains unverified |

| Base request succeeds, limit/filter fails | base_read passed, dependent checks failed/not_tested as observed, no personal-ready or fixed-access claim |
| Explicit access-diagnostic request without name | Run capability diagnostics, no identity interview or schedule creation |
| First-time setup without output preference | Propose current_snapshot and confirm it; do not promise changes-only history |

| Research fetch DisabledError, browser tool provided and allowed | Navigate same clean official query in browser, read actual body and verify; preserve failed research result separately |
| Browser identity List No103, saved List No103.000 | Compare exact decimal values, not literal formatting or imprecise floating point |
| This chat's browser path passes, target scheduled tools unknown | Browser-path success only; scheduled_runtime not_tested and no all-account compatibility claim |

| Paste START-HERE alone in normal chat, no identity | Ask only initial personal-scope question; no API calls or missing-profile failure |
| Explicit diagnostic-only request, no identity | Run access checks without identity interview or personal-lookup failure |
| Runtime text says unattended but host is normal interactive chat | Treat text as reusable contract, default to setup |
| Actual scheduled context with no private profile | Configuration error without questions or guessed identity |
