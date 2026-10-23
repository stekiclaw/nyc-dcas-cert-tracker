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

1. 先问要追踪 **个人 Certification**，还是 **机构/指定 Cert**。
2. 个人模式依次取得英文 First/Last Name、Exam No；优先用官方数据匹配 Title Code，遇到同名/多种考试时才进一步确认 MI、List No。
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

On first-time monitoring setup, the agent asks **one focused question at a time**, skips all details already provided, and **collects the user's first/last name and Exam No** (person mode). It resolves title codes from official data where possible and requests MI or exact List No only to disambiguate. An agency-only monitor instead asks agency/scope and supported certificate filters; agency focus must not be confused with promotion-list agency codes.

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

**中文：** 已知 Certification 数据集 ID 为 `a9md-ynri`，Active Lists 为 `vx8i-nprf`。Skill 现在优先直接访问官方 SODA2.1 JSON API，不再每次先搜索 Socrata Catalog。用 `curl --get --data-urlencode` 正确编码查询参数，按明确条件筛选后稳定分页，检查获取前后的记录数量，并针对超时、429/5xx 有限重试。**查询失败不代表无记录或无变化**。参见 [API 查询指南](references/api-retrieval.md)。

**English:** The Skill now prioritizes the known official SODA2.1 endpoints, with scoped filtering, stable paging, pre/post count checks, bounded retries, and explicit incomplete-data errors. Catalog discovery is only used if a dataset ID is actually unknown. See the [retrieval guide](references/api-retrieval.md).

Optional local helper (requires bash, curl and jq; no CLI is required to use the prompt-only Skill):

```bash
bash scripts/fetch-soda.sh --where "exam_no='4034' AND last_name='EXAMPLE'" --out certifications.json
python3 -m unittest discover -s tests -v  # Optional offline tests
```

**Agency attribution / 机构归属：** Certification `list_agency_code` is a promotion-list attribute, not sufficient proof of the requesting agency. For OTI/DCWP/SBS or other appointing-agency claims, require a separately verified official link; otherwise label **unverified**. The sample name above is fictional, and no live API response is implied by offline tests.
