# Guided onboarding / 引导式初始化

This is the interactive initialization contract for the prompt-only Skill. The agent asks the user for necessary search conditions once, validates them, and saves a **private, fully expanded task prompt** when a supported scheduler confirms creation. The Skill and public GitHub repository are NOT a private user database or a background daemon.

## Conversation rules / 提问规则

- When first invoked for setup, **lead with a focused question**, not a long questionnaire/form. Ask one question per turn, with a short example as needed. Record all fields volunteered in any reply and **never re-ask an answered field**. Support Chinese or English conversation; use official English spellings to match published data.
- If the user says "监控/跟踪/schedule/定期", treat recurring setup as intended. If they ask only "查询/查一下", run a one-off query and do not schedule. When unclear, first ask "想现在查询一次，还是设置定期监控？"
- **Never** request SSN, DOB, home address, employee ID or other unnecessary sensitive data. Keep real names, precise List No, and task settings out of public repository commits, issues and PRs.
- Stop prompting entirely in a scheduled/background run. A task reads the private saved settings embedded in **its own instructions**, not a previous conversation, guessed user memory or GitHub.

## Step-by-step flow / 状态机

### Step 1 — Monitoring target
- Ask: "你要跟踪自己的 Civil Service Certification，还是某个 Agency/指定 Certificate？"
- Person scope: ask official English **first and last name together**: "请提供考试登记时使用的英文 First Name 和 Last Name。" Allow an optional MI in the same reply.
- Agency-specific scope: disambiguate (a) personal certs with agency focus, (b) **promotion-list agency** certifications, or (c) known exact certificate numbers. The certification dataset's `list_agency_code` belongs to **promotion lists** and alone does not establish the agency that requested a particular certificate. Never pretend an agency-name filter proves OTI/DCWP/SBS appointing-agency coverage.
- Agency-only scope: do **not** demand a personal name. Ask the agency name, and then request exam/title or documented promotion-list code or known certificate IDs as appropriate. If appointing-agency mapping cannot be verified, offer explicit promotion-list/code tracking or exact certificate IDs, or show agency association **unverified**.

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

## Sample guided exchange / 示例（虚构姓名）

User: "帮我初始化一个每周监控 DCAS Certification 的任务。"
Agent: "你要监控自己在 Civil Service List Certification 上的记录，还是某个机构的记录？"
User: "我自己的。"
Agent: "请提供你参加考试时使用的英文 First Name 和 Last Name。"
User: "Alex Example"
Agent: "你的 Civil Service Exam No 是多少？"
User: "4034"
Agent: "我会先查官方记录确认考试 Title 和身份；如果重名，再问 List No。你想监控全部认证，还是特别关注某个机构？"
User: "全部认证，也关注 OTI。"
Agent: "可以监控所有认证，另外把 OTI 设为关注机构；但仅靠这个数据集不能可靠地确认每张证书的申请机构。你最想监控新 Certification、Cert Seq No 变化，还是都要？"
... Then ask schedule time, notification preference, summarize, and request explicit confirmation.

The example is instructional, NOT a real lookup, a real user profile, or a created task.
