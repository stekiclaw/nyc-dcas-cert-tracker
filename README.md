# NYC DCAS Cert Tracker

[中文](#中文) · [English](#english)

**无需 GitHub 插件 / No GitHub plugin needed:** [打开完整英文入口并复制提示词 / Open and copy the complete English prompt](START-HERE.md) · [纯文本 / Raw](https://raw.githubusercontent.com/stekiclaw/nyc-dcas-cert-tracker/main/START-HERE.md)

Workflow version: **2026-10-25**.

## 中文

**默认执行语言：英文。** 用户明确指定时可改用其他语言；中英文 README 均保留。

面向 ChatGPT Scheduled Tasks、网页端及其他云端 Agent 的 DCAS 认证追踪 Skill。核心工作流由提示词定义，宿主提供联网、计算、私有快照、定时和通知能力；Python 与 curl 脚本是可选执行工具，不是常驻服务。创建计划任务不代表宿主自动加载本仓库，也不保证跨次状态可用。

### 无插件快速开始

1. 用普通浏览器打开 [START-HERE.md](START-HERE.md)，复制代码块内的**全部英文指令**到 ChatGPT 并发送。无需 GitHub 账号、插件、Skill 安装或 Python。
2. ChatGPT 逐项询问缺失条件，并提供最低序号（含全部并列）、机构重点、月度批次、一年历史和变化监控选项；已有信息不重复询问。
3. 单次查询直接执行；需要定时监控时，确认设置后将**完整查询规则和私人条件**存进原任务。没有排程工具时会生成可手动粘贴到 Scheduled 的完整私人指令。
4. 官方 API 联网及可访问的私人历史快照仍须实际核验。没有历史不能可靠报告新增或排名变化；不会用聊天记忆、公开仓库或搜索摘要代替。

升级已有任务：在私聊粘贴完整入口，要求升级到 **2026-10-25**，保留原任务、排程、个人条件、语言偏好、快照引用和通知记录。仓库更新不会自动修改你的定时任务。不要把填好的私人提示词公开。

### ChatGPT Scheduled Tasks 默认入口

使用 [独立任务指令](references/scheduled-task-prompt.md)，把已确认的个人配置和私有快照引用填入任务即可；运行不要求本地 Python、clone 仓库或再次加载 GitHub。详见 [Scheduled Tasks 使用指南](references/chatgpt-scheduled.md)。默认英文，保存过的明确语言偏好优先。已有任务应更新原任务并保留历史，不重复建立。联网、私有历史存储和静默通知需以实际宿主能力为准，无法核验时明确报告限制。

Python 用户可用 `scripts/build_scheduled_prompt.py` 从私有配置生成完整任务指令；它只生成指令，不创建任务。下面的完整 Python 监控入口保留为可选执行方式。

### 功能

- 查询本人当前最低 `Cert Seq No`，保留所有并列证书；机构归属需独立官方核验。
- 跟踪指定机构相关个人批次、最近一个日历月的全部个人批次及一年可见历史。
- 对最后一次成功、同范围、带日期的快照进行比较：新增认证，同证书个人序号／包含状态、覆盖、选择条件、重发和到期日变化，以及独立确认的名单终止／延期。
- 有实质变化才通知；首次基线、数据集刷新或到期日自然经过不算新增事件。失败保持未知，不覆盖成功基线。

### 数据如何获取

只以 DCAS 官方数据和公告为事实依据。默认直接请求公有 **SODA2.1 HTTP GET**，通常无需 Token：

| 数据 | 固定接口 | 用途 |
|---|---|---|
| Certification | https://data.cityofnewyork.us/resource/a9md-ynri.json | 个人认证、序号和批次覆盖 |
| Active List | https://data.cityofnewyork.us/resource/vx8i-nprf.json | 本人名单条目与建立／周年／延长期限 |
| 官方字段与更新时间 | `https://data.cityofnewyork.us/api/views/{dataset_id}.json` | 各数据集独立 schema、`rowsUpdatedAt` |

1. 按姓名、Exam、已核验 Title Code、必要时精确十进制 List No 筛选；保留考号原始字符串，并核验前导零格式（例如 `04034` / `4034`）。姓名相同不足以合并身份。
2. 使用 URL 编码的 `$where`、`$select`、稳定 `$order`、`$limit=1000`、`$offset` 分页至完整。Active List 使用自己的真实字段和排序。
3. 分页前后按**完全相同过滤条件**获取 `count(*) as total`；验证每页 JSON 数组、预期行数及总数，并复核前后 `rowsUpdatedAt`。不一致则丢弃该次结果。稳定排序与计数降低并发刷新风险，不能视为数据库事务快照。
4. 超时、408、429、5xx 进行有界重试；400 检查官方字段；DNS/出站网络错误在实际执行宿主诊断。失败不等于零记录或无变化，不自动替换为 SODA3、Catalog、第三方或搜索摘要。
5. 比较私有快照，分别记录认证事件日、数据更新时间、查询时间及已通知事件键。新增查询字段本身不是已有字段发生变化。

详见 [API 查询指南](references/api-retrieval.md) 和 [数据解释规则](references/data-and-reporting.md)。

### 执行工具与网络边界

如选择在具备 Python 和 HTTPS 出站能力的私有宿主运行，可使用完整的标准库监控入口：

```bash
python3 scripts/dcas_monitor.py \
  --config /private/config.json \
  --state /private/state.json \
  --report /private/report.json
```

从 [虚构配置示例](references/private-config.example.json) 建立私有配置。完整入口包含 Certification + Active List、metadata 稳定性与分页计数校验、全部并列最低序号、月／年历史、批次覆盖比较、通知去重及私有原子快照。默认无变化及首次基线静默；`--digest` 输出英文完整报告。支持旧私有快照显式迁移，避免重置历史。详见 [完整 Python 指南](references/python-monitor.md)。

下面的小脚本仍可用于仅抓取个人 Certification：

```bash
python3 scripts/fetch_certifications.py \
  --first-name ALEX --last-name EXAMPLE \
  --exam 4034 --title-code 13621 --list-no 123.500 \
  --out /private/certifications.json
```

身份为虚构示例。该 helper 获取个人 Certification 并做计数、分页、身份校验及私有原子写入；完整监控仍需宿主按指南补充 metadata 前后复核、Active List、批次覆盖、时间窗口计算及历史对比。可选 List No 当前在 Python helper 中按 Decimal 本地过滤，计数对应过滤前的 API 范围；自行构造 GET 时可按官方字段类型将 List No 加入 `$where`，首尾计数必须使用同一条件。

终端可使用 `curl --get --data-urlencode`；另有需要 bash/curl/jq 的 `scripts/fetch-soda.sh`。无终端的宿主可请求正确编码的官方 URL。网页搜索工具无法读取接口，不代表该宿主所有 HTTP 工具都不可用；一个运行器成功或失败，也不能代表另一个运行器。

```bash
python3 scripts/check_api_network.py
python3 -m unittest discover -s tests -v
```

网络探测和离线测试不证明真实个人监控已执行。公开 GitHub Actions 仅用于不含私人候选人信息的连接／合成测试；不得提交真实姓名、监控参数、个人结果、日志或快照。脚本语言或 Token 不能解除平台的网络策略。不要关闭 TLS 校验或硬编码 IP 绕过限制。

### 使用与计划任务

首次设置按 [引导流程](references/onboarding.md) 一次询问一个缺失条件，主动提供全部个人认证、机构重点、最低序号、月度批次、一年历史和变化监控功能。已提供的信息不重复询问。标准 Agency 选项仍是**本人**相关认证，非整个机构所有候选人。

有明确排程意图并确认配置后，使用 [独立任务模板](references/task-templates.md) 将完整条件存入任务**私有指令**。每次自动运行使用这些条件，不重新初始化；只有宿主确认创建成功才称任务已启用。可靠变化提醒还必须有可访问的私有历史快照；没有历史时只能建立新基线，不得假称变化。

**解释限制：** `Cert Seq No` 是该证书内序号。`list_agency_code/desc` 不足以单独证明请求认证的机构；无独立官方关联就标记“招聘／任命机构未核验”，保留原字段。不同证书序号差不是同证书内升降。认证、reachability、provisional replacement、人数及名单号范围不能证明实际聘用、Permanent Appointment 或 tie-breaker 结果。

## English

**English is the default execution/report language**, unless the user explicitly requests another language.

A prompt-based NYC DCAS certification Skill for ChatGPT Scheduled Tasks, browser agents and other cloud hosts. The host supplies HTTP access, computation, private checkpoints, scheduling and notifications. Python and curl helpers are optional tools, not a background service. Scheduling does not guarantee that the host loads this repository or retains prior results.

### No-plugin quick start

1. Open [START-HERE.md](START-HERE.md) in a regular browser and paste the **entire English code block** into ChatGPT. No GitHub account/plugin, Skill installation or Python is required.
2. Answer one missing setup question at a time; choose minima/all ties, agency focus, monthly batches, annual history and/or change monitoring. Already supplied inputs are reused.
3. One-off queries run immediately. For monitoring, confirm the setup and save the **complete runtime rules plus private profile** in the task. If scheduling tools are unavailable, receive a fully filled private prompt for manual setup in Scheduled.
4. Verify direct official API access and private checkpoint availability on the executor. Without accessible history, changes remain unknown; chat memory, search snippets and a public repository are not substitutes.

To upgrade, paste the complete entry in a private chat and request version **2026-10-25**, retaining the existing task, schedule, identity, language override, checkpoint reference and notified events. Repository updates do not update live tasks automatically. Never publish a completed private prompt.

### ChatGPT Scheduled Tasks default entry

Use the [standalone task instructions](references/scheduled-task-prompt.md) with the confirmed private profile and checkpoint reference embedded. Scheduled execution does not require Python, a cloned repository or reloading GitHub. See the [Scheduled Tasks guide](references/chatgpt-scheduled.md). Default to English and preserve explicit saved language preferences. Upgrade an existing task in place and keep its history. Verify actual HTTP, private state and silent-completion capabilities; disclose missing capabilities.

Optional `scripts/build_scheduled_prompt.py` fills the template from a private config; it does not schedule anything. The full Python monitor remains available for capable private hosts.

### Features

- Current personal minimum `Cert Seq No`, including every tied certificate; independently verify agency attribution.
- Agency-focused personal batches, all batches issued in the past calendar month and one-year observed histories.
- Verified changes to certificates, personal sequence/inclusion within the same certificate, coverage, selection, reissue/expiry, and independently confirmed list termination/extension.
- Material-change alerts with deduplication. A baseline, dataset refresh or calendar expiry passage alone is not a new event. Failed retrieval remains unknown and preserves the last successful checkpoint.

### Retrieval and reliability

Use the fixed official **SODA2.1 GET** endpoints above, normally without a mandatory token. Filter by exact candidate/exam/verified title and, when needed, exact decimal List No. Preserve exam text and check leading-zero variants; never merge identities using names alone.

Use encoded `$where`, `$select`, a deterministic `$order`, `$limit=1000` and `$offset`. Validate every JSON array and page length, initial/final counts under the identical filter, and dataset `rowsUpdatedAt` before/after. Reject inconsistent attempts. Ordering and counts reduce race risk but do not provide transaction-level snapshot isolation. Check Active List separately using its own schema.

Retry transient transport/408/429/5xx failures with limits; inspect official metadata on 400. Record actual DNS/HTTP errors. Do not substitute SODA3, Catalog, search snippets or third-party results. Distinguish row-level event dates, source update times and observation times. A newly selected field is not evidence that its value changed historically.

Use `scripts/fetch_certifications.py` on a private Python host with official-domain HTTPS access, or curl / correctly encoded official URLs where supported. The smaller acquisition helper verifies candidate rows, paging and counts and writes private JSON atomically. For optional Python-host monitoring, use `python3 scripts/dcas_monitor.py --config /private/config.json --state /private/state.json --report /private/report.json`. This complete entry point includes metadata stability, Active Lists, minimum/month/year analysis, coverage comparisons, checkpoint migration and report deduplication. It is English-first and silent for an unchanged result or initial baseline; use `--digest` for a full report. See the [full Python guide](references/python-monitor.md) and [fictional config example](references/private-config.example.json). The smaller acquisition helper alone does not perform these monitoring steps. Its optional List No filter currently runs locally using Decimal; the API counts apply before that local filter. For a direct GET with List No in `$where`, use that same predicate for both counts.

Network capability is executor-specific. A failed web-search fetch does not establish that direct HTTP is blocked, and an external CI success does not grant access to a scheduled host. Run `scripts/check_api_network.py` on the actual executor. Offline tests and privacy-safe connectivity smoke tests are not proof of a successful personal query. Keep real identities, filled task profiles, snapshots and results out of public commits, CI logs and artifacts. Never disable TLS checks or hard-code an IP to evade network policy.

### Setup and interpretation

Follow [guided onboarding](references/onboarding.md), ask one missing setting at a time and skip already supplied inputs. Offer all personal certificates versus agency-focused **personal** records, not agency-wide research by default. After explicit scheduling intent and confirmed configuration, save a complete [standalone private task prompt](references/task-templates.md). Unattended runs reuse it without questions. A reliable change claim requires an accessible, dated, successful prior checkpoint of the same scope; otherwise establish a baseline.

`list_agency_code/desc` alone is insufficient to identify a requesting agency. Preserve published fields and label the requesting/appointing agency unverified without independent official evidence. Cross-certificate sequence differences are not movement within one certificate. Certification, reachability, provisional-replacement flags, counts and list ranges do not prove hiring, Permanent Appointment or tie-breaking outcomes.

## Files

- [Scheduled Tasks guide](references/chatgpt-scheduled.md) and [standalone runtime prompt](references/scheduled-task-prompt.md): default cloud task entry.
- [scripts/build_scheduled_prompt.py](scripts/build_scheduled_prompt.py): optional private prompt generator.
- [START-HERE.md](START-HERE.md): complete English copy-and-paste workflow for users without a GitHub plugin.
- [SKILL.md](SKILL.md): interactive and unattended behavior.
- [API retrieval](references/api-retrieval.md): requests, completeness and network diagnosis.
- [Data and reporting](references/data-and-reporting.md): official fields, identity, windows and interpretation.
- [Onboarding](references/onboarding.md): guided setup.
- [Task templates](references/task-templates.md): standalone private scheduling instructions.
- [Acceptance scenarios](references/acceptance-scenarios.md): prompt behavior checks.
- [scripts/dcas_monitor.py](scripts/dcas_monitor.py): complete English-first private monitoring CLI.
- [Python monitor guide](references/python-monitor.md): configuration, migration, evidence and notification boundaries.
- `scripts/`: smaller acquisition, curl and network helpers remain available.
- `tests/`: offline helper tests; `agents/openai.yaml`: host metadata.

Official datasets: [Certifications](https://data.cityofnewyork.us/d/a9md-ynri) · [Active Lists](https://data.cityofnewyork.us/d/vx8i-nprf).
