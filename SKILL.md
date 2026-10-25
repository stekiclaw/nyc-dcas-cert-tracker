---
name: nyc-dcas-cert-tracker
description: Prompt-only NYC DCAS personal certification and active-list queries for ChatGPT web Scheduled Tasks. Use for current minimum Cert Seq No with all ties, agency-focused records, monthly batches, one-year visible history and verified changes from accessible previous task results. English by default; no external storage, scripts or deployed backend.
---

# NYC DCAS Cert Tracker

Version 2026-10-25.2. Execute with ChatGPT web tools only. Do not require GitHub integration, installed scripts, files, databases, private checkpoint services or external compute. ChatGPT's ordinary saved task instructions and outputs are the only possible history source; no guarantee that earlier outputs are accessible.

## Entry and setup

For users without an installed Skill, provide [START-HERE.md](START-HERE.md): one complete English copy-and-paste workflow. It includes all setup and runtime instructions; no repository loading is needed later.

Follow its setup interactively, asking one missing question at a time and reusing supplied values. Offer all own certs versus agency-focused personal certs; current minimum/all ties, month, one-year visible records and optional changes. Default English unless explicitly overridden. Never start onboarding in scheduled runs. Use [data-and-reporting.md](references/data-and-reporting.md) for official sources and interpretation.

Preflight base_read, pagination, filtering and completeness separately before calling the workflow usable. Record passed/failed/not_tested. Test prior_result_access for change claims; scheduled_runtime remains not_tested until an actual scheduled execution succeeds. For explicit diagnostic-only requests, run these checks without identity onboarding or task creation. Do not replace an unsuccessful monitor with an unrequested diagnostic schedule. Default the proposed output mode to current_snapshot unless the user selected otherwise. A source page or count probe alone is not a successful personal lookup. DisabledError without HTTP status is a tool-level failure. Strip UTM/tracking keys from operational requests and preserve identity predicates. A prompt cannot add blocked/missing tools.

## Scheduled execution

Embed the completed private profile plus the entire [scheduled runtime](references/scheduled-task-prompt.md) in the task. Require no checkpoint_reference. Use the user's agreed current_snapshot or verified_changes policy. Prefer a same-chat task when supported, but promise no automatic access to all previous outputs. Create/update a task only after successful preflight and the user's scheduling authorization; otherwise provide accurate failure/manual instructions. Keep existing task IDs, schedules and personal choices during an authorized upgrade. Do not alter live tasks merely because repository files changed.

Compute minima from complete ALL-agency personal rows with all ties, expiry unknown separately, and numeric sequence checks. Agency associations need independent official evidence; promotion-list agency fields alone do not identify a requesting agency. Fetch only the data needed for selected checks; fetch exact batch coverage when comparing coverage, not whole-exam data for every lookup.

## History and notifications

Use accessible successful dated ChatGPT results of the same identity and scope only. Do not use memory or an unseen task run as a snapshot. Report currently visible one-year batches separately from observed within-certificate history. Preserve the distinction between a cross-batch sequence difference and movement within one cert.

Use the headline “Comparison unavailable” when prior values/complete sets are inaccessible; never “No verified change” or an overall no-change claim. Current rows support later comparison only if actually readable then. Deduplicate only against accessible reported transitions; promise no durable event log or exactly-once delivery. Normal run evidence tables may support later comparisons but are not external state and may not be readable later. Silence only under the actual runtime contract and complete comparable results. Follow the saved policy rather than silently replacing changes-only with a digest.

Keep certification, actual hire and Permanent Appointment separate. See [acceptance scenarios](references/acceptance-scenarios.md) for manual evaluation. No script test suite proves real Scheduled Tasks access; inspect a real scheduled run on the user's account.
