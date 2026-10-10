---
name: nyc-dcas-cert-tracker
description: Query and monitor official NYC DCAS active lists and certifications by candidate name, exam and title. Use for smallest current Cert Seq No across agencies including all ties, candidate position at a named agency, past-month certification batches, one-year agency position history, and meaningful certification or list change alerts.
---

# NYC DCAS Cert Tracker

## Ask which functions are needed

Respond in the user's language. On interactive invocation, proactively offer these functions and allow multiple choices:
1. Find agencies with the smallest current personal Cert Seq No, including every tied agency and certificate.
2. Track personal certification positions at specified agencies.
3. List all agencies and certificate batches containing the candidate in the past calendar month, with each Cert Seq No.
4. Analyze one year of certification positions at a specified agency.
5. Monitor meaningful certification, coverage, personal sequence, list-status and expiry changes, notifying only on material changes.

If the user already chose functions, execute them and briefly offer the remaining functions without blocking. In scheduled/noninteractive runs use saved choices and never ask questions.

Collect missing First Name, Last Name, MI if present, exam number, title/title code and target agencies for agency-specific work. Strongly recommend exact List No to disambiguate names. Do not request SSN, DOB, address or employee ID. Resolve an unknown title code from official records; do not hard-code personal inputs. For Computer Associate (Operations), scope exam 4034/04034 AND title code 13621. Historical exams can reuse a number for unrelated titles.

Resolve exact normalized name, MI and List No in official Active records. If multiple identities match, present minimal distinguishing values and ask for selection before personal conclusions. If Active has no match, inspect certification records separately; do not declare removal or appointment. Normalize case and surrounding whitespace, never silently fuzzy-match or transliterate.

## Query official sources

Read [references/data-and-reporting.md](references/data-and-reporting.md). Use only DCAS pages/notices and DCAS-owned NYC Open Data for facts. Use the bundled Python standard-library script for deterministic retrieval and calculations:

```bash
python scripts/dcas_cert.py person --exam EXAM --title-code CODE --first FIRST --last LAST --as-of YYYY-MM-DD --output /absolute/path/person.json
```

Add --mi, --list-no and --agency-code only when known. For global minima and monthly reports use all agencies; an agency-filtered query cannot establish the global minimum. Set as-of to the actual date in America/New_York. Optional --input accepts API-format snapshot JSON with active and certifications arrays; report its age and never label it live. Uploaded official CSV exports may be analyzed with equivalent rules after inspecting their headers; filenames do not prove freshness or authenticity.

The script returns resolved identities, current tied minima, unknown-expiry records, recent-month records, older certificates reissued in that month, annual histories grouped by agency and all personal rows. candidate_ambiguous prohibits personal conclusions. Preserve data update timestamps and observation date. Query/schema failures are unknown results, never “no changes.”

## Interpret positions carefully

Call cert_seq_no the candidate's sequence within that certification, not global rank, hiring priority, reachability or appointment order. Keep list_no separate and preserve decimal values. A batch is a distinct cert_issue_no within exam/title/agency; a request date can contain several certificates. Include special selection criteria and reissue dates.

For current, default to issued certificates whose expiry date is on/after the as-of date. Include expiry-today records with a label. This is date-based observation, not administrative validity or eligibility. Exclude missing expiry dates from confirmed-date minima and list them as current status unknown. If there are no unexpired records, say so and offer historical positions as historical.

Compute the numeric minimum over all qualifying current personal rows. List EVERY matching row and EVERY tied agency, including several tied certificates at one agency. Explain that batch sizes and selection criteria limit cross-agency comparison.

Use cert_date for monthly/yearly history; flag older certificates reissued during the window separately. Include all same-day batches. Show chronological sequences, published counts, changes and gaps. A lower sequence means earlier within that batch only. Never attribute a change to hires or removals without evidence. Compare first/latest and best/worst observed values; do not interpolate missing history. Distinguish between different-batch sequence differences and within-certificate changes observed in two dated snapshots.

Strictly separate certification, actual hire and Permanent Appointment. no_certified, no_vacancies, provisional_replacement, coverage and sequence do not prove hires, reachable status or permanent appointment. Min/max List No does not imply every intervening number is included.

## Monitor and retain state

Create recurring tasks only when explicitly requested; reuse an existing matching task. Query-only use does not authorize scheduling. Use available Automations tools with the user's timezone; do not claim continuous monitoring without them.

```bash
python scripts/dcas_cert.py monitor --exam EXAM --title-code CODE --as-of YYYY-MM-DD --previous /absolute/path/previous.json --output /absolute/path/current.json
```

Omit --previous for the first baseline. Save current snapshot and last successful snapshot durably outside the skill. Use stable keys (exam, title, agency, cert_issue_no, sel_cert_description), complete distinct List No sets, sequences and dates. Add personal row comparisons from person mode when selected. Save selected functions, user inputs, query date, dataset timestamps and notified event keys privately, preserving existing file identity. Never bundle real names, candidate results, credentials or user history in this reusable skill.

Alert on new certificates/agencies, material coverage or personal-sequence changes, reissues, expiry changes and independently confirmed list termination/extension. First baseline, source update timestamp alone, or the passage of an expiry date alone is not a new agency action. Do not repeat unchanged events. Verify missing records before claiming termination; failed queries must not overwrite the last successful snapshot.

Include agency, cert number, request/issue dates, old/new coverage or personal sequence, expiry, official links, query date and source update dates. Separate facts from same-score-group implications; group_no is not automatically a tie group. When there is no meaningful change, suppress notification using the runtime skip marker if required. Keep ongoing tracking enabled until the user stops it or its objective ends.
