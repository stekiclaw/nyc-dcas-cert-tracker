# Guided onboarding / 引导式初始化

This is the interactive initialization contract for the prompt-only Skill. The agent asks the user for necessary search conditions once, validates them, and saves a **private, fully expanded task prompt** when a supported scheduler confirms creation. The Skill and public GitHub repository are NOT a private user database or a background daemon.

## Conversation rules / 提问规则

- When first invoked for setup, **lead with a focused question**, not a long questionnaire/form. Ask one question per turn, with a short example as needed. Record all fields volunteered in any reply and **never re-ask an answered field**. Support Chinese or English conversation; use official English spellings to match published data.
- If the user says "监控/跟踪/schedule/定期", treat recurring setup as intended. If they ask only "查询/查一下", run a one-off query and do not schedule. When unclear, first ask "想现在查询一次，还是设置定期监控？"
- **Never** request SSN, DOB, home address, employee ID or other unnecessary sensitive data. Keep real names, precise List No, and task settings out of public repository commits, issues and PRs.
- Stop prompting entirely in a scheduled/background run. A task reads the private saved settings embedded in **its own instructions**, not a previous conversation, guessed user memory or GitHub.

## Step-by-step flow / 状态机

### Step 1 — Choose the scope of **your own** certifications / 选择个人监控范围
- **Opening question (ask verbatim in Chinese when the user speaks Chinese):** "你想跟踪自己的 Civil Service Certification，还是自己在某个 Agency 下的认证记录？"
- The choices mean **(a) all certifications belonging to the user** (save `mode: person_all`) and **(b) that same user's certifications related to a specific Agency** (save `mode: person_agency_focus`). The second choice **does not mean all employees/candidates at that agency**. Never offer agency-wide monitoring as the default alternative.
- If the user chooses their **entire personal record**, ask next: "请提供你参加考试时登记的英文 First Name 和 Last Name。" Optional MI may be included.
- If the user chooses **their record under a specified Agency**, and has not yet named it, ask next: "你想关注哪个 Agency？请提供名称或常用缩写（例如 OTI、DCWP、SBS）。" After the agency is known, ask for **their** official English first and last name, followed by Exam No as below. If an agency was already named, skip the agency-name question.
- An Agency name is a **reporting/attribution preference**, not a verified `$where` filter: `list_agency_code` identifies promotion-list context and **does not** establish the certificate's requesting/hiring agency. Always retrieve the user's matching certificates without that agency-code filter. Show a record as associated with the selected Agency only with independent official evidence; otherwise mark agency association **unverified** and warn that Agency-only coverage/notifications cannot be guaranteed from this dataset alone.
- **Advanced exception:** If the user explicitly asks to research agency-wide certifications unrelated to their own name, separately clarify promotion-list-code vs verified certificate-ID scope. That is a different workflow and must not override the two personal options above.

### Step 2 — Exam and identity
For personal tracking, ask, in order, only missing values:
1. Official English first and last name (plus optional MI).
2. Civil Service **Exam No**, kept as text with leading zeros preserved.
3. Look up matching exam/title records directly in the official API. Do **not require the user to know Title Code** in advance; derive the code/description if one verifiable choice exists and ask for confirmation. If multiple choices, ask them to pick one. If API fails, mark title unverified instead of inventing it.
4. Ask for exact decimal **List No** and/or MI only when identity is ambiguous or user opts in for stronger matching. Never merge two people who share a name. Do not turn decimal List No into floating-point approximations.
For agency-only tracking, instead obtain agency name and supported filter type plus exact certificate IDs or verified promotion-list code; optional exam/title narrows scope.

### Step 3 — Checks and focus
Ask which events to track, without requiring knowledge of raw API fields:
- **Default:** new personal certifications and material changes to the same certificate (reissue, expiration and coverage).
- Optional: currently valid minimum `Cert Seq No` across **all matching certificates** (retain all ties).
- Optional: recent one-month activity, one-year observed history, Active List status.
- Optional: named certificates / a specified agency as a **focus**; actual appointing-agency association requires independent official evidence. Personal all-certificate queries must NOT be filtered by promotion-list agency code.

### Step 4 — Schedule and notifications
For recurring setup only, ask **cadence** (daily, weekly, or custom) and then **when** (day and time or daypart), if not yet given. Suggest weekly as a reasonable choice for weekly-updated public data; do not invent a fixed hour. Use timezone `America/New_York` by default unless the user chooses another. Ask whether to notify **verified changes only** (default when user delegates) or send a **regular digest**. First successful fetch is a baseline, not proof of a new event. For one-time lookup skip cadence/time/notification questions.

### Step 5 — Preflight and final confirmation
- Run a preflight against known `a9md-ynri`/`vx8i-nprf` endpoints if available. Fetch only the selected datasets, filter candidate/exam/title, validate complete responses, and use official metadata if fields have changed. Never repeatedly search Socrata Catalog.
- If **multiple candidates match**, ask a disambiguating question before scheduling. If a **verified zero match**, confirm spelling and exam, then offer to monitor *future* entries with `zero_match_user_confirmed` status. If the API is unavailable, show `not_verified` and offer a draft rather than claiming validation.
- Show a short **configuration summary**: mode; name (if any), exam, verified title, optional List No, agency focus/filter and provenance, selected checks, cadence/day/time/timezone, and notification policy.
- Ask one explicit final question: "确认按这些条件创建监控任务吗？" Create or update only on confirmation using the host's *actual supported scheduling action*. If an equivalent task already exists and is accessible, offer update rather than duplicate. Claim success only after the host confirms; otherwise supply a privately filled standalone prompt for manual setup.

### Step 6 — Save the profile inside the scheduled task
When the host supports scheduled tasks, include the **full validated settings as literal values inside the task's private prompt**, together with the complete query and notification instructions from [task-templates.md](task-templates.md). The scheduler stores its own prompt; the Skill does not provide persistent storage. All real candidate information stays private; **never commit a filled profile to public GitHub**.

Illustrative **unfilled / synthetic** profile fields:

~~~yaml
profile_version: 1
mode: person_all     # person_all | person_agency_focus | agency_promotion_list | cert_ids
candidate:
  first_name: Alex
  last_name: Example
  mi: null
  exam_no: "4034"    # exact text; do not strip leading zeros
  title_code: null   # verified from official source or left unverified
  title_description: null
  list_no: null      # decimal string
agency:
  focus_name: null
  filter_type: none  # none | verified_cert_ids | promotion_list_code
  cert_issue_nos: []
  promotion_list_agency_code: null
  attribution_evidence: null
checks: [new_cert, material_changes, global_minimum]
schedule:
  cadence: weekly
  day_time: USER_SELECTED
  timezone: America/New_York
notification_policy: changes_only # changes_only | digest
preflight_status: verified        # verified | zero_match_user_confirmed | not_verified
~~~

## Automatic execution / 之后的每次定时触发

1. Read the **saved task-specific configuration**. **Do not** initiate onboarding or ask identity/agency/schedule questions again.
2. Build SoQL with exact name, Exam No and confirmed title/list fields; agency restrictions **only** when documented by explicit evidence mode. Escape string literals and URL-encode all parameters. Query `a9md-ynri` and, if opted in, `vx8i-nprf` directly; count-check and paginate completely.
3. Compare the current verified result to a **previous verified checkpoint only if the host actually provides persistent task history/state**. If not, report an as-of snapshot and disclose that historical change comparisons cannot be guaranteed. Saved prompts alone do not save data snapshots.
4. On API error, missing/ambiguous identity or partial fetch: mark the state **unknown/incomplete**, preserve any accessible last successful checkpoint, and **never** report "no change" based on failure. On first successful run establish the baseline.
5. Apply the saved notification policy and avoid repeated event alerts where the host has real deduplication state. Do not claim hiring/permanent appointment, and never invent a requesting-agency label.

## Changing a saved monitor / 修改已保存配置

If the user later says "添加考试、改为每天、修改机构、暂停或删除", retrieve the accessible matching task/profile, change **only** the requested fields after confirmation, and retain the remaining saved filters. If the host cannot access an existing task, ask the user for the privately saved task details; do not fabricate task IDs. Keep different exams/candidates isolated in separately named tasks unless the user explicitly wants them combined.

## Sample guided exchanges / 首次提问与模拟回答（虚构姓名）

**Opening Agent question, same for both examples:**
Agent: "你想跟踪自己的 Civil Service Certification，还是自己在某个 Agency 下的认证记录？"

**Example A — 全部个人 Certification**
User: "我想跟踪自己全部的 Certification。"
Agent: "请提供你参加考试时登记的英文 First Name 和 Last Name。"
User: "Alex Example"
Agent: "你的 Civil Service Exam No 是多少？"
User: "4034"
Agent: "我会核验考试 Title 和个人记录。你想关注新增 Certification、Cert Seq No 变化，还是两者都要？"

**Example B — 自己在指定 Agency 下的 Certification**
User: "我只想跟踪自己在 OTI 的 Certification。"
Agent: "好的，已把 OTI 记录为关注的 Agency。请提供你参加考试时登记的英文 First Name 和 Last Name。"
User: "Alex Example"
Agent: "你的 Civil Service Exam No 是多少？"
User: "4034"
Agent: "我会查询你的个人认证记录，并核验能否从独立官方资料确认哪些认证与 OTI 有关。如果无法确认，我会明确标记，而不会把所有认证误当作 OTI 认证。你想跟踪新认证、Cert Seq No 变化，还是两者都要？"

**Example C — 仅表示想指定 Agency，尚未给出名称**
User: "只关注某个 Agency。"
Agent: "你想关注哪个 Agency？例如 OTI、DCWP 或 SBS。"
User: "DCWP"
Agent: "请提供你参加考试时登记的英文 First Name 和 Last Name。"

Then ask about schedule time and notifications, show the configuration summary, and request explicit confirmation. Never repeat an already-known name, exam or agency.

The example is instructional, NOT a real lookup, a real user profile, or a created task.
