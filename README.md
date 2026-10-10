# NYC DCAS Cert Tracker

[中文](#中文) · [English](#english)

## 中文

基于 NYC DCAS 官方公开数据的候选人认证位置查询与追踪 Skill。支持不同考试和职位；仓库不包含任何用户的个人数据。

### 功能

1. 查询当前 Cert Seq No 最小的机构，列出全部并列机构及对应认证批次。
2. 查询或持续追踪指定机构中的个人认证序号。
3. 列出最近一个日历月出现的所有机构、认证编号和个人序号。
4. 总结指定机构过去一年内各认证批次的序号变化。
5. 监测新增认证、覆盖范围、名单状态和到期日期变化；没有实质变化时不通知。

交互使用时会主动询问需要哪些功能。用户已明确选择时直接执行；定时运行不再提问。

### 安装和使用

将整个仓库作为 `nyc-dcas-cert-tracker` 文件夹安装到支持 `SKILL.md` 的助手环境。Codex 可放在 `~/.codex/skills/nyc-dcas-cert-tracker/`；其他环境按其 Skills 安装流程启用。

```text
$nyc-dcas-cert-tracker
查询我的当前最低认证序号、最近一个月的认证批次，以及指定机构过去一年的位置变化。
```

准备以下输入：

- First Name、Last Name，以及 MI（如有），按官方记录拼写。
- 考试编号和职位名称或 Title Code。
- 目标机构（机构查询和年度分析需要）。
- 准确 List No（建议，用于排除同名）。

不需要提供 SSN、生日、住址或员工编号。

### 查询脚本

要求 Python 3.9+，只使用标准库，不需要 GitHub、DCAS 或 Socrata API Key。运行环境需允许访问 NYC Open Data。持续通知需要助手环境提供任务调度；运行脚本本身不会创建定时任务。

```bash
python scripts/dcas_cert.py person \
  --exam 4034 --title-code 13621 \
  --first YOUR_FIRST_NAME --last YOUR_LAST_NAME \
  --output person.json
```

按需加入 `--mi`、`--list-no`、`--agency-code` 或 `--as-of YYYY-MM-DD`。日期省略时使用纽约当天日期。全机构最低序号和月度查询不要加机构过滤。

首次建立监测基线：

```bash
python scripts/dcas_cert.py monitor \
  --exam 4034 --title-code 13621 --output baseline.json
```

后续比较：

```bash
python scripts/dcas_cert.py monitor \
  --exam 4034 --title-code 13621 \
  --previous baseline.json --output current.json
```

查询成功后，由助手环境保存新状态作为下一次基线；失败时不要覆盖最后一次成功记录。个人序号持续追踪还需保存并比较 `person` 输出。快照、姓名和个人结果放在仓库外，不要提交到 GitHub。

### 字段与解读

| 字段 | 含义 |
|---|---|
| `list_no` | 考试名单号 |
| `cert_issue_no` | 认证编号；不同编号代表不同认证 |
| `cert_seq_no` | 该认证中的候选人序号，不是实际聘用顺序或全局排名 |
| `cert_date` | 认证签发日期，区别于申请日期和考试名单建立日期 |
| `cert_expiration_date` | 认证到期日，区别于考试名单到期日 |

“当前”按已签发且到期日不早于查询日筛选；这不能证明行政有效性或个人任用资格。缺失到期日的记录单列为状态未知。不同批次人数和筛选条件可能不同，年度序号差异不等于同一份认证内的位置变化，也不能证明有人已获聘。

**名单认证、实际聘用与 Permanent Appointment 必须分别确认。** 序号、人数、Provisional Replacement 标志和名单范围不能单独证明 reachable、实际聘用或永久任用。最小／最大名单号不表示中间所有人均在该认证中。

考试编号可能在不同年代重复使用，必须同时过滤 Title Code。例如 Computer Associate (Operations) 为考试 4034/04034、Title Code 13621。

### 数据与文件

使用下方列出的官方来源。脚本核验分页完整性和查询期间的数据更新情况。报告分别注明查询日期、官方数据更新时间及认证事件日期。

- `SKILL.md`：助手执行与主动提问流程。
- `scripts/dcas_cert.py`：官方查询和确定性计算。
- `references/data-and-reporting.md`：字段、日期规则和报表格式。
- `agents/openai.yaml`：Skill 界面元数据。

## English

A skill for querying and tracking a candidate's certification sequence using official NYC DCAS public data. It supports different exams and civil service titles. This repository contains no user-specific personal data.

### Features

1. Find agencies with the lowest current Cert Seq No, including every tied agency and matching certification.
2. Query or track the candidate's certification sequence at selected agencies.
3. List every agency, certification number and personal sequence observed in the past calendar month.
4. Summarize one year of certification sequences at a selected agency.
5. Monitor new certifications, coverage, list status and expiration changes; notify only when meaningful changes occur.

During interactive use, the skill proactively asks which features are needed. It proceeds directly when the user has already selected them. Scheduled runs use saved choices without asking questions.

### Installation and use

Install the entire repository as a folder named `nyc-dcas-cert-tracker` in an assistant environment that supports `SKILL.md`. For Codex, use `~/.codex/skills/nyc-dcas-cert-tracker/`. Follow the host's skill installation procedure in other environments.

```text
$nyc-dcas-cert-tracker
Find my lowest current certification sequence, list my certifications from the past month, and summarize my one-year sequence history at a selected agency.
```

Provide:

- First Name, Last Name and Middle Initial (MI), if present, as recorded officially.
- Exam number and civil service title or Title Code.
- Target agencies for agency-specific queries and annual analysis.
- Exact List No, recommended to distinguish candidates with the same name.

Do not provide an SSN, date of birth, address or employee ID.

### Query script

Requires Python 3.9+ and uses only the standard library. No GitHub, DCAS or Socrata API key is required. The environment must have access to NYC Open Data. Ongoing notifications require a scheduling capability in the assistant host; running the script does not create a scheduled task.

```bash
python scripts/dcas_cert.py person \
  --exam 4034 --title-code 13621 \
  --first YOUR_FIRST_NAME --last YOUR_LAST_NAME \
  --output person.json
```

Add `--mi`, `--list-no`, `--agency-code` or `--as-of YYYY-MM-DD` when needed. The date defaults to the current date in New York. Do not filter by agency when finding the global minimum or listing all agencies from the past month.

Create the first monitoring baseline:

```bash
python scripts/dcas_cert.py monitor \
  --exam 4034 --title-code 13621 --output baseline.json
```

Compare a subsequent observation:

```bash
python scripts/dcas_cert.py monitor \
  --exam 4034 --title-code 13621 \
  --previous baseline.json --output current.json
```

After a successful query, the assistant host should retain the new state as the next baseline. Never overwrite the last successful state after a failed query. Tracking personal sequences also requires saving and comparing `person` outputs. Keep snapshots, names and personal results outside this repository; do not commit them to GitHub.

### Fields and interpretation

| Field | Meaning |
|---|---|
| `list_no` | Exam list number |
| `cert_issue_no` | Certification identifier; different identifiers represent different certifications |
| `cert_seq_no` | Candidate sequence within that certification, not hiring order or global rank |
| `cert_date` | Certification issue date, distinct from the request date and exam list establishment date |
| `cert_expiration_date` | Certification expiration date, distinct from the exam list expiration date |

“Current” means issued certifications with an expiration date on or after the query date. This date-based filter does not establish administrative validity or individual eligibility. Records with missing expiration dates are shown separately as unknown. Batch sizes and selection criteria can differ, so annual sequence differences do not establish movement within the same certification or prove that other candidates were hired.

**Certification, actual hiring and Permanent Appointment require separate confirmation.** Sequence numbers, counts, Provisional Replacement flags and coverage alone do not prove reachability, hiring or permanent appointment. Minimum and maximum list numbers do not imply that every intervening candidate appears on a certification.

Exam numbers can be reused in different years. Always filter by Title Code as well. For example, Computer Associate (Operations) uses exam 4034/04034 and Title Code 13621.

### Data and files

Use the official sources below. The script checks pagination completeness and whether data changes during retrieval. Reports distinguish the query date, official dataset update time and certification event date.

- `SKILL.md`: Assistant workflow and proactive feature selection.
- `scripts/dcas_cert.py`: Official queries and deterministic calculations.
- `references/data-and-reporting.md`: Fields, date rules and report formats.
- `agents/openai.yaml`: Skill interface metadata.

## 官方来源 / Official sources

- [Civil Service List Certification](https://data.cityofnewyork.us/City-Government/Civil-Service-List-Certification/a9md-ynri)
- [Civil Service List (Active)](https://data.cityofnewyork.us/City-Government/Civil-Service-List-Active-/vx8i-nprf)
