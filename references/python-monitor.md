# Complete private Python monitor

## Run

Use Python 3.9+ with the system IANA timezone database (including America/New_York), the standard library and official-domain HTTPS access. No pip packages, database or persistent web server are required. Keep configuration, state and reports outside the repository in a private directory.

```bash
mkdir -p /private/dcas
cp references/private-config.example.json /private/dcas/config.json
# Edit the private copy with the candidate's exact official identity.
python3 scripts/dcas_monitor.py \
  --config /private/dcas/config.json \
  --state /private/dcas/state.json \
  --report /private/dcas/report.json
```

The example identity is fictional. Store Exam No and List No as strings; an unspecified MI is `null`, while `""` explicitly requires an empty MI. Title Code and exact List No are mandatory for this fully disambiguated executable workflow. Initial interactive Skill setup can resolve them before writing the private config.

Default stdout is **English**, silent for a first baseline or unchanged observation. `--emit-baseline` prints the initial baseline without calling it a change. `--digest` prints the complete English report on every successful run. `--as-of YYYY-MM-DD` overrides today's New York date for reproducible interpretation; it does not retrieve a historical dataset version.

Exit `0` means complete verification succeeded (including silent no-change/baseline runs); exit `2` means verification incomplete. On failure inspect stderr and preserve the last successful state. A separate report JSON is written on every successful run, even when stdout is empty. A host can translate user-facing text if explicitly requested; raw official field values stay unchanged. The script itself always emits English diagnostics/report prose.

## Included workflow

- Direct official SODA2 GET, scoped by exact name, exam text variants, title and decimal List No; bounded transient retries and optional `SODA_APP_TOKEN` header.
- Independent schema and metadata checks for Certification and Active List; default 1,000-row pages, deterministic ordering, page-length/count verification, duplicate-projection detection and dataset update stability checks within and across queries.
- Complete exam/title certification coverage without other candidates' names; personal certification rows and personal Active List dates.
- All current minimum-sequence ties, unknown expiry and missing sequence separately (a missing sequence prevents a proved global dated minimum); issue dates must have arrived and expiry dates include the as-of day.
- All personal issues in the last calendar month, annual issued-batch histories from current source rows, older certificates reissued during either window, and explicitly linked agency-focus histories. Retain dated personal/Active observations privately for one year when row values change, so earlier observed sequences or subsequently missing certificates remain auditable. History before the first available checkpoint cannot be reconstructed as prior observations.
- Same-certificate sequence/inclusion/coverage/selection/reissue/expiry comparisons, private reports/checkpoints, observation-scoped event keys (allowing legitimate repeated transitions), and no alerts for source timestamps, first baseline or elapsed expiry alone.
- Raw List Agency fields retained without inferring the requesting agency. Missing certificates or Active rows are observations requiring confirmation, never proof of removal, hire or termination.
- Private atomic writes (`0600`) and an exclusive state lock. After a crash, inspect the lock's PID and running processes before manually removing a stale `.lock`; do not run concurrent writers.

Ordering/counts/timestamps reduce pagination races; SODA2 is not a transactionally pinned snapshot. If duplicate projected rows appear, verification fails conservatively rather than claiming completeness.

## Independent official evidence

The executable cannot establish semantic agency associations or independently review every DCAS notice from dataset codes alone. The host must read official evidence and save verified links privately:

```json
{
  "agency_links": [
    {
      "cert_issue_no": "80001",
      "agency_name": "Example verified appointing agency",
      "source_url": "https://www.nyc.gov/example-official-evidence",
      "verified_at": "2026-10-24"
    }
  ],
  "list_notices": [
    {
      "notice_id": "example-notice",
      "kind": "extension",
      "effective_date": "2026-10-24",
      "verified_at": "2026-10-24",
      "source_url": "https://www.nyc.gov/example-official-notice"
    }
  ]
}
```

These are **nonexistent illustrative links and synthetic records**, not actual notices. A valid official URL is necessary but does not prove its contents support the association: the host must verify content and exam/title applicability. `kind` is `termination` or `extension`. New/changed independently verified notices are compared with prior saved notices; list anniversary/extension fields alone do not generate confirmed termination claims. Existing confirmed notices on an initial baseline are retained without a new-event alert.

`focus_agencies` highlights only certificates with independently verified mappings; an empty result means association/coverage unverified, not that the agency never certified the candidate. Unknown agency records remain available and are not merged into an invented agency history. The report labels cross-certificate differences as separate-batch observations, never hiring/eligibility/tie-breaker conclusions.

## Existing state and notifications

Reuse the same config/state paths for recurring runs. The script does not create a scheduler or send email/messages. A supported task host runs it, reads the report, interprets official notices and delivers notifications. Default output and the repository Skill are English unless the user explicitly requests another language.

For the older private tracker JSON containing `personal_tracking.checkpoint`, `active_candidate_observation` and `coverage_checkpoint.snapshot.certificates`, import into a **new** state path:

```bash
python3 scripts/dcas_monitor.py \
  --config /private/dcas/config.json \
  --migrate-from /private/dcas/legacy-state.json \
  --state /private/dcas/state-v1.json \
  --report /private/dcas/report.json
```

The import verifies identity/scope and complete dated ALL-agency observations, rejects ambiguous aggregated rows, retains prior legacy notification records, and does not reset history. It never overwrites an existing destination. An unsupported checkpoint must be migrated explicitly; do not silently replace it with a new baseline. Legacy event IDs are retained for audit; new event hashes operate on imported observations, so unchanged imported certificates produce no new alerts.

Event keys record **local report generation, not confirmed external delivery**. Report JSON is written before the state is advanced; if host delivery later fails, replay the saved report through the host's delivery mechanism. The script does not provide a transactional external-message outbox or delivery acknowledgement. Do not change identity scope in place or reuse state files across candidates.

The earlier `fetch_certifications.py` remains a smaller acquisition-only helper. It does not replace `dcas_monitor.py` for full monitoring.

## Validation

```bash
python3 -m unittest discover -s tests -p test_dcas_monitor.py -v
python3 scripts/dcas_monitor.py --help
```

Tests use synthetic in-memory official-response fixtures and temporary private paths. No real candidate identity, results or filled profile belongs in public GitHub Actions, logs or artifacts. A live host still needs working HTTPS access; tests do not grant it.
