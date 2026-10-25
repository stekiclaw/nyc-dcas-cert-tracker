# NYC DCAS Cert Tracker

[中文](#中文) · [English](#english)

**[开始使用 / Copy the full English prompt](START-HERE.md)**

Version **2026-10-25.2** · Default output: **English**

## 中文

在用户自己的 **ChatGPT 网页版计划任务**中查询 NYC DCAS 官方认证与有效名单。复制完整提示词即可开始配置；无需 GitHub 插件、Python、外部持久存储、服务器或额外云端计算服务。计算由 ChatGPT 执行，配置和普通运行结果保留在 ChatGPT 中。

### 使用

1. 打开 [START-HERE.md](START-HERE.md)，复制代码块内全部英文提示词到 ChatGPT。
2. 回答缺失条件并选择功能；已有姓名、考试、机构等不重复询问。个人数据只填在自己的私人对话／任务中。
3. 先直接验证官方 API、身份及完整查询。成功后，确认排程和输出方式，由可用工具创建计划任务；没有排程工具时使用生成的完整私人指令手动建立任务。
4. 支持时优先在同一聊天中排程，并检查第一次实际定时运行。普通聊天成功不保证定时运行工具相同。

### 能力预检与发布状态

逐项报告 `base_read`（基础正文）、`pagination`（分页）、`filtering`（身份筛选）、`completeness`（完整性）、`prior_result_access`（历史结果）、`scheduled_runtime`（真实定时执行），状态为 passed／failed／not_tested。基础读取成功不代表个人查询可用。可单独要求“只诊断访问”，无需先提供姓名，也不会自动创建任务。

**当前已知限制：** 测试帐号的无参数接口成功，带筛选／分页参数的网页请求返回 DisabledError；尚无该帐号完整定时运行成功的证据。本版发布的是提示词流程，未宣称解决该访问问题。流程和文档检查通过，与目标帐号实际运行成功分别报告。

### 功能和输出方式

- 当前最低个人 Cert Seq No，列出全部并列证书；缺失到期日／序号单独说明。
- 指定机构相关个人认证、最近一个日历月的全部个人批次。
- 当前官方数据中可见的一年批次历史；不同批次的序号差，不是同证书内升降。
- `current_snapshot`：每次提供选定的当前核验结果，适合无法确认历史访问能力时。
- `verified_changes`：只有可读取的上次成功、同范围、带日期结果才能证明变化；缺失时报告 `Comparison unavailable`。仅当可读取已报告事件时才能避免重复通知。

### 必须知道的限制

**本项目不能给帐号增加联网工具。** 若干净的官方 JSON 请求仍返回 `DisabledError`，且没有其他可用直接工具，该帐号当前无法运行本流程。搜索到数据集页面不代表查到了个人记录；失败不得写无变化。不要反复改提示词声称已修复权限。

**不使用外部持久存储，因此不保证完整历史、去重或可靠变化提醒。** 任务只能比较本次实际可读取的此前 ChatGPT 运行结果。名单当前可见的一年历史，不等于持续保存一年的个人排名快照。首次观察不是新增事件；无法访问历史不是无变化。不要求用户部署后端来补足这些限制。

实际 API 请求必须移除 `utm_source`、`utm_*` 等追踪参数，保留身份条件。显示的引用链接不一定等于工具实际请求；无 HTTP 状态的工具错误不能当成 DCAS400/403。

只以 DCAS 官方页面、公告和其 NYC Open Data 为事实依据。`list_agency_code/desc` 是 promotion-list 属性，不能单独证明请求机构。认证、序号、人数、范围及 provisional replacement 不能证明实际聘用、Permanent Appointment、可直接聘用或同分组全部被选中。重大名单终止／延期需独立官方确认。

### 升级与项目范围

用完整入口升级原任务指令，保留任务 ID、排程、个人条件、功能和明确语言偏好。移除旧的外部快照、部署和 Python 前提；旧外部数据不自动删除，仓库更新不自动修改任务。

本版已移除 Python／curl 脚本、脚本测试、GitHub Actions、部署／私有配置和外部快照指南；旧实现仍可从 Git 历史找到。以前的脚本测试通过不能证明本版在所有帐号的 Scheduled Tasks 中可用。本版只提供提示词和人工验收场景，真实运行能力必须在目标帐号验证。

## English

Run official NYC DCAS personal certification and Active List checks in the user's own **ChatGPT web Scheduled Tasks**. Copy the full prompt; no GitHub plugin, Python, deployed backend, external persistent storage or additional cloud-compute service is required. ChatGPT performs the computation and retains its ordinary task instructions/results.

### Start

1. Open [START-HERE.md](START-HERE.md), paste the entire English code block into ChatGPT and supply only missing private settings.
2. Choose minimum/all ties, agency focus, monthly batches, one-year visible history and/or qualified changes. Verify direct official data and identity first.
3. After a successful preflight, confirm schedule and policy. Use available scheduling tools or manually paste the fully configured private runtime instructions into Scheduled. Prefer the same chat where supported; verify the first actual scheduled run.

### Capability checks and release status

Report base_read, pagination, filtering, completeness, prior_result_access and scheduled_runtime separately as passed/failed/not_tested. Basic body access does not prove personal lookup readiness. Ask “diagnose access only” to test without an identity interview or task creation. Interactive success leaves scheduled_runtime not_tested.

**Known limitation:** the tested account could read the unparameterized endpoint, while filtered/paginated web requests returned DisabledError. Complete scheduled execution on that account remains unverified. This is a prompt-workflow release, not a claim that access restrictions have been fixed. Report document/behavior validation separately from live account compatibility.

### Two policies

`current_snapshot` returns selected verified as-of results each run. `verified_changes` requires actually accessible successful dated earlier ChatGPT results of matching scope. If history is missing, report “Comparison unavailable,” not no change. Deduplication is possible only against accessible reported events; full historical tracking and exactly-once alerts are not promised. One-year currently visible batch records are not a year of monitored within-certificate sequence changes.

### Capability boundary

A prompt cannot add network tools. If the actual web executor cannot retrieve clean official API JSON, this workflow is unavailable on that account. Dataset search results are not personal data retrieval. No external checkpoint storage is required or created, so history access can be incomplete. Do not claim all-account compatibility, guaranteed silent notifications or successful monitoring after a failed query. Strip tracking parameters from operational API URLs; distinguish malformed HTTP queries from tool-level DisabledError.

Use only official DCAS evidence. Promotion-list agency fields do not establish the requesting agency. Certification, counts, list ranges and sequence numbers do not prove hiring, eligibility, Permanent Appointment or tie-breaking. Independently confirm major list termination/extension.

### Upgrade and scope

Replace the existing task instructions after authorization, preserving ID, identity, schedule, selected checks and explicit language. Remove external-state/backend/script requirements without deleting legacy external data. This repository update does not update live tasks.

This release removes executable scripts/tests, GitHub Actions and deployment/storage/configuration guides. Legacy code remains in Git history. Prior script test results do not establish this prompt-only release's real scheduled compatibility.

## Files and official sources

- [START-HERE.md](START-HERE.md): complete English setup + runtime prompt; no later repository loading.
- [SKILL.md](SKILL.md): optional installed Skill entry.
- [Scheduled runtime](references/scheduled-task-prompt.md): task contract copied in full during setup.
- [Data and reporting](references/data-and-reporting.md): official fields and interpretation.
- [Acceptance scenarios](references/acceptance-scenarios.md): manual behavior evaluation, not a claim of live platform success.
- `agents/openai.yaml` and `assets/icon.svg`: optional Skill UI metadata.

Official datasets: [Certification](https://data.cityofnewyork.us/d/a9md-ynri) · [Active List](https://data.cityofnewyork.us/d/vx8i-nprf).
