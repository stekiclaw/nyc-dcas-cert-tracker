# NYC DCAS Cert Tracker — Prompt-Based Skill

[中文](#中文) · [English](#english)

## 中文

**定位：** 面向 ChatGPT 网页端 Scheduled Tasks、Meta Muse 等云端 Agent 的轻量 `SKILL.md`。**不依赖 Python、数据库、Docker 或本地后台程序。** 宿主负责联网、定时执行、状态访问与通知；Skill 定义 DCAS 数据核验、人员序号分析和重要变化通知规则。

### 功能
- 全部机构当前个人最低 `Cert Seq No`，保留所有并列机构与批次。
- 指定机构各 Cert 批次个人位置、最近一个日历月的全部批次及一年历史。
- 对多次可信快照进行比较，发现新增认证、同批次个人位置变化、重发/到期/覆盖变化；过滤无实质意义的变动。
- 在**用户明确要求**后帮助宿主创建独立计划任务；自动运行只使用已保存的私有查询条件，不反复提问。

### 首次初始化：逐步引导式提问

首次设置时，Agent **逐轮提问**，不会一次要求填写所有字段，也不会重复询问用户已经提供的信息：

1. **固定首次提问：**“你想跟踪自己的 Civil Service Certification，还是自己在某个 Agency 下的认证记录？”两种选项都只跟踪**用户本人**；前者查全部个人认证，后者重点关注本人在指定机构下的认证，**不是**跟踪该 Agency 的所有候选人。
2. 若选定 Agency 却尚未给出名称，则先询问 Agency；接着两种模式都依次取得英文 First/Last Name、Exam No，优先用官方数据匹配 Title Code，遇到同名/多种考试时才进一步确认 MI、List No。
3. 根据需求设置 **全部 Certification、指定证书、特定机构重点关注**，选择监控的变化类型。机构名称不一定能直接转为官方 API 筛选条件；不能验证机构归属就明确标记。
4. 按用户选择询问执行频率与时间、时区、仅变化时通知或定期报告，展示**配置摘要**，用户确认后才创建/更新任务。

**创建成功后，完整过滤条件保存在任务私有指令中**，每次计划运行时自动使用，**不再重复问姓名/考试编号**。宿主如果无法保存跨次结果，只能每次出具当前快照，不能保证历史变化提醒。完整规则见 [引导式初始化](references/onboarding.md) 与 [计划任务模板](references/task-templates.md)。

### 网页端计划任务
1. 交互调用 `SKILL.md`，按 [初始化流程](references/onboarding.md) 逐轮收集并核验必要条件，不要求用户预先知道 Title Code。
2. 用户确认配置摘要后，用 [独立计划任务模板](references/task-templates.md) 创建任务；姓名、Exam、机构范围、频率、通知策略均保存在任务私有指令中（不提交公开仓库）。
3. 宿主若能持久访问前次结果，则比较最后一次成功快照；否则只做当前查询，**不能**宣称检测到了历史变化。计划任务运行不代表宿主自动加载 GitHub Skill。
4. 使用 [测试场景](references/acceptance-scenarios.md)验收首次运行、并列名次、无变化、数据失败和历史比较等行为。

**注意：** 所谓后台持续追踪是由宿主按计划重复执行，而不是 Skill 自行常驻。具体频率、通知和跨次状态能力以宿主实际支持为准。不要把真实候选人信息加入公开仓库。

官方来源：[Certifications](https://data.cityofnewyork.us/d/a9md-ynri) · [Active Lists](https://data.cityofnewyork.us/d/vx8i-nprf)。

## English

A **prompt-only Skill** for browser/cloud agents, including ChatGPT Scheduled Tasks and agents such as Meta Muse. It does not require a local Python runtime, database, hosted server or custom crawler. The **host** performs the browsing, scheduling, history access and notifications; the Skill specifies how to query official NYC DCAS data, interpret certification sequences and detect verified material changes.

### Features
- Global current personal minimum `Cert Seq No` across agencies, with every tied certificate.
- Agency-specific sequences, past-calendar-month certificates, and one-year observed histories.
- Careful comparison of verified dated observations for meaningful changes, without conflating certification with hiring or permanent appointment.
- Standalone [scheduled-task prompt](references/task-templates.md) to paste into hosts that cannot auto-load `SKILL.md`; [evaluation scenarios](references/acceptance-scenarios.md) for acceptance.

### Guided first-run setup

The first question always offers a choice between **tracking all of the user's own Civil Service Certifications** and **tracking that same user's Certifications associated with a specific Agency**. It does **not** offer agency-wide monitoring by default. Ask for the Agency name only if the second option was chosen without specifying it; in either mode, ask one focused question at a time for the user's official first/last name and Exam No, skipping fields already supplied. Resolve title codes from official data where possible, requesting MI or exact List No only for disambiguation. Agency associations need independent verification: promotion-list agency codes are not enough.

The agent then asks what to track, cadence/time, notification mode, previews a configuration summary and creates a task **only after explicit confirmation**. The task's **private self-contained prompt** stores all validated filters for subsequent automated executions; future runs do **not** restart the interview. Reliable historical change detection also requires genuinely persisted snapshots beyond the prompt. See [guided onboarding](references/onboarding.md) and [scheduled task template](references/task-templates.md).

### Setup
Use the Skill interactively, determine exam/title/candidate criteria and requested functions, then create a separate recurring host task **only with explicit user scheduling intent**. Supply the standalone task prompt with privately entered parameters and cadence. A baseline is not a change alert; a failed fetch is not "no changes." A host unable to retrieve past run evidence cannot guarantee reliable longitudinal change alerts.

Official sources: [DCAS Certifications](https://data.cityofnewyork.us/d/a9md-ynri) · [DCAS Active Lists](https://data.cityofnewyork.us/d/vx8i-nprf).

## Files
- `SKILL.md`: main interactive/scheduled agent behavior.
- `references/data-and-reporting.md`: official fields, comparators and report definitions.
- `references/onboarding.md`: guided interactive initialization and saved-profile contract.
- `references/task-templates.md`: self-contained cloud scheduling prompt with privately saved filters.
- `references/acceptance-scenarios.md`: prompt-only acceptance scenarios.
- `agents/openai.yaml`: compatible skill metadata.

**Portability:** Custom Skill auto-loading is host-dependent. Scheduling is a host capability, not a promise made by this repository.

## API 获取成功率优化 / Reliable API retrieval

**默认 API 方案：SODA2.1 GET**。对公有数据不强制要求 Token；定时查询使用 `$where` 精确匹配姓名、Exam No、Title Code（必要时 List No），加上 `$select`、`$order`、`$limit`/`$offset`。不以 `SEARCH "姓名"` 替代身份核验。不把 SODA3 或第三方网页用作自动 fallback；官方接口失败就明确报告未验证。详见 [API 指南](references/api-retrieval.md)。

**中文：** 已知 Certification 数据集 ID 为 `a9md-ynri`，Active Lists 为 `vx8i-nprf`。Skill 现在优先直接访问官方 SODA2.1 JSON API，不再每次先搜索 Socrata Catalog。用 `curl --get --data-urlencode` 正确编码查询参数，按明确条件筛选后稳定分页，检查获取前后的记录数量，并针对超时、429/5xx 有限重试。**查询失败不代表无记录或无变化**。参见 [API 查询指南](references/api-retrieval.md)。

**English:** The Skill now prioritizes the known official SODA2.1 endpoints, with scoped filtering, stable paging, pre/post count checks, bounded retries, and explicit incomplete-data errors. Catalog discovery is only used if a dataset ID is actually unknown. See the [retrieval guide](references/api-retrieval.md).

Optional local helper (requires bash, curl and jq; no CLI is required to use the prompt-only Skill):

```bash
bash scripts/fetch-soda.sh --where "exam_no='4034' AND last_name='EXAMPLE'" --out certifications.json
python3 -m unittest discover -s tests -v  # Optional offline tests
```

**Agency attribution / 机构归属：** Certification `list_agency_code` is a promotion-list attribute, not sufficient proof of the requesting agency. For OTI/DCWP/SBS or other appointing-agency claims, require a separately verified official link; otherwise label **unverified**. The sample name above is fictional, and no live API response is implied by offline tests.


## API 网络故障诊断 / Network failure diagnostics

**中文：** 遇到 `curl: (6) Could not resolve host: data.cityofnewyork.us`，应先检测当前运行环境的 DNS 与 HTTPS 出站连接，而不是改 SoQL 语法、把 SODA2 换成 SODA3 或申请 Token。运行：

```bash
python3 scripts/check_api_network.py
```

该检查只查询一个非个人的官方 JSON 示例，不包含候选人姓名。也可以通过 [GitHub Actions Connectivity Smoke Test](https://github.com/stekiclaw/nyc-dcas-cert-tracker/actions/workflows/soda2-connectivity.yml) 在单独的 GitHub 运行器验证。**2026-10-23 GitHub Actions 测试成功：DNS 正常，SODA2 返回 HTTP 200 JSON 数组。** 这证明某个外部运行器能访问 API，**不等于 ChatGPT 的定时任务也具备网络权限**。本项目无法修改 ChatGPT 平台的网络策略；若任务环境确实封锁外部连接，需要让实际数据获取在具有 HTTPS 出站权限的受信任私有环境运行。不要把个人监控条件、姓名或结果保存到公开 CI 日志/Artifact。

**English:** If `curl (6)` occurs, diagnose DNS and outbound HTTPS **on the actual executor** before changing API URLs or adding tokens. Use `python3 scripts/check_api_network.py` or the public connectivity-only GitHub Actions smoke test. A GitHub-hosted run successfully reached SODA2 on October 23, 2026, but this does not grant egress access to the ChatGPT scheduled task environment. Keep candidate identities and results out of public CI logs and artifacts. See [network triage](references/api-retrieval.md#networkdns-failure-triage-and-proven-alternate-runner).


## Python SODA2 抓取 / Python candidate retrieval

**默认建议：** 如果实际运行器具备外部 HTTPS 访问权限，可使用纯 Python 标准库的 [个人认证抓取脚本](scripts/fetch_certifications.py)，无需 `curl`、`jq`、第三方 Python 包或 SODA3 App Token。它只使用官方 SODA2 GET，支持姓名/Exam/Title 精确筛选、`04034` / `4034` 号码格式、List No 十进制比较、分页、首尾 `count(*)` 校验、有界重试和原子写入权限为 `0600` 的私有 JSON。

```bash
python3 scripts/fetch_certifications.py \
  --first-name ALEX --last-name EXAMPLE \
  --exam 4034 --title-code 13621 --list-no 103.000 \
  --out /path/to/private/certifications.json
```

注意：示例身份为**虚构**。输出包含候选人信息，必须保存在私有目录；**不要把真实姓名/数据写入公开的 GitHub Actions YAML、CI 日志、Artifact 或 Git commit**。

[GitHub Actions Python SODA2 Smoke Test](https://github.com/stekiclaw/nyc-dcas-cert-tracker/actions/workflows/soda2-connectivity.yml) 在具有互联网出站访问的 GitHub 托管运行器上执行 5 个离线测试、官方域名连接和虚构姓名筛选查询。2026-10-23 已成功完成，但**尚未使用真实私人候选人配置运行认证数据抓取**。ChatGPT 当前 Python 容器仍存在 DNS/HTTPS 出站限制；单纯切换脚本语言不能解除该限制。

**English:** On an egress-enabled private host, use `python3 scripts/fetch_certifications.py --first-name ALEX --last-name EXAMPLE --exam 4034 --title-code 13621 --list-no 103.000 --out /private/path.json`. It requires only Python's standard library, uses official SODA2 filtered GET, count and page verification, and writes private JSON atomically with 0600 permissions. Never publish actual candidate settings or output to a public CI workflow, log or artifact. GitHub Actions smoke tests run with a **fictional** name only.
